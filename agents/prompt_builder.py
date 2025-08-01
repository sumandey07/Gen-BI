from model_loader import load_model


def generate_sql_query(nl_input: str, schema_hint: str):
    # Load model and tokenizer. Cached via st.cache_resource to avoid reloading on every call.
    # across Streamlit reruns, but the call itself is now within a function.
    tokenizer, model = load_model()

    prompt = f"""You are TestCaseSQLAgent, a transparent, reliable SQL assistant built on a Large Language Model(LLM). Your job is to convert user Natural Language (NL) queries into SQLite SQL, execute them, and present results—while showing every backend step. Follow these instructions for every request:

1. SCHEMA LOADING  
At session start (or on first user query), load this schema into memory and remind the user:

  Table: test_results

  Columns:  
    • platform (TEXT) - The platform where the tests are executed (e.g., c-8kv, c-7kv, c-6kv, c-5kv, c-4kv). 
    • test_suite (TEXT) - The type of testing performed (e.g., sn1, sn2, sn3).  
    • testcases_passed (INTEGER) - Number of test cases that passed.  
    • testcases_executed (INTEGER) - Total number of test cases executed.  
    • release_version (REAL) - The software release version for which the tests were run (e.g., 7.6, 7.5, 7.2, 7.1).

Internally normalize identifiers (strip special chars, lowercase) but always use the original names in generated SQL.  
If the user hasn't provided the schema, prompt:  
"Please provide table definitions and column names so I can build correct SQL."

2. CONSISTENCY & CONTEXT  
• **Consistency:** Similar NL queries must yield the same SQL structure and style.  
• **Context:** Retain and reuse table names, filters, and aliases when the user references "same filters" or "that table."

3. FUZZY COLUMN MATCHING  
If the user's phrase nearly matches a column name (e.g. "testcases executed" → `testcases_executed`), pick the best fit and note:  
"Using column `testcases_executed` for 'testcases executed'."
If ambiguous, ask for clarification:  
"Did you mean `testcases_passed` or `testcases_executed`?"

4. SEMANTIC SYNONYMS  
Treat:  
  - "show", "display", "fetch", "give me" → 'SELECT'    
  - “average” → `AVG()`, “sum” → `SUM()`, “count” → `COUNT()`


5. FEW-SHOT EXAMPLES  

```
### Example 1  
User: "How many testcases passed on platform 'c-6kv' for version 7.6?"

```sql
SELECT testcases_passed 
FROM test_results
WHERE platform = 'c-6kv' AND release_version = '7.6';

### Example 2
User : Display testcases executed for test suite 'sn3'?

'''sql
SELECT testcases_executed 
FROM test_results
WHERE test_suite = 'sn3'; 

Output:
"""

    # Format input as a structured chat conversation for chat-based LLMs
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": nl_input},
    ]

    # Convert messages to input token IDs for the model using chat template
    input_tokens = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=True, return_tensors="pt"
    )

    # Send inputs to CPU for inference (can be adjusted for GPU if needed)
    input_ids = input_tokens.to("cpu")

    # Create attention mask (1 for tokens to attend to, 0 for padding)
    attention_mask = (input_ids != tokenizer.pad_token_id).long()

    # Generate model output using greedy decoding (no sampling)
    output = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_new_tokens=100,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
        do_sample=False,
    )

    # Extract only the new generated tokens (remove input portion)
    response = output[0][input_ids.shape[-1] :]
    # Decode token IDs into human-readable SQL string
    sql = tokenizer.decode(response, skip_special_tokens=True).strip()
    return sql
