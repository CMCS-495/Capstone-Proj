#!/usr/bin/env python3
import argparse
import importlib
import sys
from pathlib import Path

try:
    from transformers import pipeline
except ImportError:  # pragma: no cover - optional dependency
    pipeline = None


def _load_real_pipeline():
    """Attempt to import the real transformers.pipeline, bypassing the stub."""
    global pipeline
    try:
        import transformers  # type: ignore
        repo_root = Path(__file__).resolve().parents[1]
        stub_dir = repo_root / "transformers"
        src_dir = repo_root / "LLM" / "transformers" / "src"
        if Path(getattr(transformers, "__file__", "")).resolve().parent == stub_dir:
            for module_name in list(sys.modules.keys()):
                if module_name.startswith("transformers"):
                    sys.modules.pop(module_name, None)
            if str(stub_dir) in sys.path:
                sys.path.remove(str(stub_dir))
            if str(src_dir) not in sys.path:
                sys.path.insert(0, str(src_dir))
            pipeline = importlib.import_module("transformers").pipeline
        else:
            pipeline = transformers.pipeline
    except Exception:
        pipeline = None

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

def main():
    parser = argparse.ArgumentParser(
        description="LLM client using Hugging Face Transformers"
    )
    parser.add_argument(
        "prompt",
        help="Prompt string to send to the LLM"
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=120,
        help="Number of new tokens to generate (default: 120)"
    )
    parser.add_argument(
        "--num_return_sequences",
        type=int,
        default=1,
        help="Number of responses to generate (default: 1)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)"
    )
    parser.add_argument(
        "--top_p",
        type=float,
        default=0.9,
        help="Top-p (nucleus) sampling (default: 0.9)"
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Device ID for inference (e.g., 0 for GPU). If omitted, uses CPU."
    )
    args = parser.parse_args()

    llm = pipeline(
        "text-generation",
        model=MODEL_NAME,
        device=args.device
    )

    outputs = llm(
        args.prompt,
        max_new_tokens=args.max_new_tokens,
        num_return_sequences=args.num_return_sequences,
        do_sample=True,
        temperature=args.temperature,
        top_p=args.top_p,
        return_full_text=False
    )

    for out in outputs:
        text = out["generated_text"].strip()
        # Ensure we end on a full sentence
        if "." in text:
            text = text[: text.rfind(".") + 1]
        print(text)


def _get_llm_pipeline(device: int = None):
    """
    Factory for downstream calls (e.g. generate_description) to reuse the same settings.
    """
    if pipeline is None:
        _load_real_pipeline()
    if pipeline is None:
        raise RuntimeError("transformers package is required for LLM features")
    return pipeline(
        "text-generation",
        model=MODEL_NAME,
        device=device
    )

# Lazy‐initialized singleton
_LLM = None

def generate_description(kind: str, context: dict, max_new_tokens: int = 120) -> str:
    """
    kind: one of 'gear', 'enemy', 'room', etc.
    context: dict with fields relevant to that kind.
    Returns a single, concise, one-sentence description.
    """
    global _LLM
    if _LLM is None:
        _LLM = _get_llm_pipeline(device=None)

    # Build a clear one-sentence prompt (no Markdown)
    if kind == 'gear':
        prompt = (
            f"Describe this RPG item in one full sentence:\n"
            f"Name: {context.get('name')}\n"
            f"Stats: {context.get('stats')}\n\n"
            f"Description:"
        )
    elif kind == 'enemy':
        prompt = (
            f"Describe this enemy in one full sentence:\n"
            f"Name: {context.get('name')}\n"
            f"Level: {context.get('level')}\n\n"
            f"Description:"
        )
    elif kind == 'room':
        prompt = (
            f"Describe this room scene in one full sentence:\n"
            f"Prompt: {context.get('prompt')}\n\n"
            f"Description:"
        )
    else:
        prompt = (
            f"Describe {kind} with context {context} in one full sentence:\n\n"
            f"Description:"
        )

    outputs = _LLM(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        num_return_sequences=1,
        return_full_text=False
    )

    desc = outputs[0].get('generated_text', '').strip()
    # If model echoed the prompt exactly, return empty string
    if desc == prompt.strip():
        return ""
    # Truncate at last period so we don't end mid-sentence
    if "." in desc:
        desc = desc[: desc.rfind(".") + 1]
    return desc


if __name__ == "__main__":
    main()
