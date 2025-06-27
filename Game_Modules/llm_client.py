#!/usr/bin/env python3
import argparse
from transformers import pipeline

def main():
    parser = argparse.ArgumentParser(description="LLM client using Hugging Face Transformers")
    parser.add_argument("prompt", help="Prompt string to send to the LLM")
    parser.add_argument(
        "--max_length",
        type=int,
        default=50,
        help="Maximum tokens to generate (default: 100)"
    )
    parser.add_argument(
        "--num_return_sequences",
        type=int,
        default=1,
        help="Number of responses to generate (default: 1)"
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Device ID for inference (e.g., 0 for GPU). If omitted, uses CPU."
    )
    args = parser.parse_args()

    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    llm = pipeline(
        "text-generation",
        model=model_name,
        device=args.device
    )

    outputs = llm(
        args.prompt,
        max_length=args.max_length,
        num_return_sequences=args.num_return_sequences
    )

    for out in outputs:
        print(out["generated_text"])


def _get_llm_pipeline(device: int = None):
    # you can tweak model name / parameters here
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    return pipeline(
        "text-generation",
        model=model_name,
        device=device
    )

# Lazy‐initialized singleton
_LLM = None

def generate_description(kind: str, context: dict, max_new_tokens: int = 50) -> str:
    """
    kind: one of 'gear', 'enemy', 'room', etc.
    context: dict with whatever fields are relevant (e.g. name, stats, prompt)
    """
    global _LLM
    if _LLM is None:
        _LLM = _get_llm_pipeline(device=None)

    # build a simple prompt based on kind
    if kind == 'gear':
        prompt = (
            f"Describe this item for a fantasy RPG:\n"
            f"Name: {context['name']}\n"
            f"Stats: {context['stats']}\n\n"
            f"Description:"
        )
    elif kind == 'enemy':
        prompt = (
            f"Write a flavor description for this enemy:\n"
            f"Name: {context['name']}\n"
            f"Level: {context['level']}\n\n"
            f"Description:"
        )
    elif kind == 'room':
        prompt = (
            f"Describe this room scene:\n"
            f"Prompt: {context['prompt']}\n"
            f"Neighbors: {context['neighbors']}\n\n"
            f"Description:"
        )
    else:
        prompt = (
            f"Describe {kind} with context {context}:\n\n"
            f"Description:"
        )

    # ask the model, but tell it NOT to return the prompt text
    outputs = _LLM(
        prompt,
        max_new_tokens=max_new_tokens,
        num_return_sequences=1,
        return_full_text=False
    )

    desc = outputs[0]['generated_text'].strip()
    
    # fallback: if model still echoes the prompt, strip it
    if desc.startswith(prompt):
        desc = desc[len(prompt):].strip()

    return desc

if __name__ == "__main__":
    main()
