import torch
from config import MODEL_NAME
from transformers import AutoTokenizer, AutoModelForCausalLM
import streamlit as st


@st.cache_resource  # Add this decorator to cache the loaded model and tokenizer
def load_model(model_name=MODEL_NAME):
    """
    Loads the Hugging Face tokenizer and model.
    Uses st.cache_resource to cache the model, loading it only once across Streamlit reruns.
    """
    print(f"Loading model '{model_name}' (this should happen only once)...")

        # Load the tokenizer for the specified model
    tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Load the model with appropriate tensor type depending on device availability
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )

        # Set model to evaluation mode
    model.eval()

        # Move model to GPU if available, otherwise keep on CPU
    if torch.cuda.is_available():
        model.to("cuda")
    return tokenizer, model
