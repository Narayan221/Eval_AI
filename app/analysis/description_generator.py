from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os
import torch

class DescriptionGenerator:
    def __init__(self):
        self.model_path = "models/flan-t5-small"
        if not os.path.exists(self.model_path):
            raise RuntimeError(f"Model not found at {self.model_path}. Please run scripts/download_t5.py first.")
            
        print(f"Loading DescriptionGenerator from {self.model_path}...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"DescriptionGenerator using device: {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, local_files_only=True)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path, local_files_only=True).to(self.device)

    def generate(self, title: str) -> str:
        prompt = f"generate a short, engaging description for a video session titled: {title}"
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)
        
        outputs = self.model.generate(
            input_ids, 
            max_length=50, 
            num_beams=4, 
            early_stopping=True,
            no_repeat_ngram_size=2
        )
        
        description = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return description
