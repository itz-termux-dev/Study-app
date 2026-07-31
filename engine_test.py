import os
import subprocess

MODEL_PATH = os.path.expanduser("~/study_app/models/llm_model.gguf")
VOICE_PATH = os.path.expanduser("~/study_app/models/voice.onnx")
PIPER_BIN = os.path.expanduser("~/study_app/piper/piper")
LLAMA_BIN = os.path.expanduser("~/study_app/llama.cpp/build/bin/llama-cli")

def test_llm():
    print("--- 1. Testing Local Offline LLM ---")
    prompt = "Explain why the sky is blue in 2 simple sentences."
    print(f"Prompt: {prompt}\nGenerating response...\n")

    # Command using updated --no-display-prompt flag
    cmd = [
        LLAMA_BIN,
        "-m", MODEL_PATH,
        "-p", prompt,
        "-n", "128",
        "-c", "2048",
        "--temp", "0.7",
        "--no-display-prompt"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        response = result.stdout.strip()
        print(f"AI Output: {response}\n")
        return response
    except Exception as e:
        print(f"LLM Execution Error: {e}")
        return None

def test_tts(text):
    print("--- 2. Testing Local Voice TTS ---")
    output_wav = "output.wav"
    cmd = f'echo "{text}" | grun {PIPER_BIN} --model {VOICE_PATH} --output_file {output_wav}'
    os.system(cmd)

    if os.path.exists(output_wav):
        print(f"\nSuccess! Audio synthesized and saved to: {output_wav}")

if __name__ == "__main__":
    ai_response = test_llm()
    if ai_response:
        test_tts(ai_response)

