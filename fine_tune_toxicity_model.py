from transformers import XLMRobertaForSequenceClassification, XLMRobertaTokenizer, Trainer, TrainingArguments
from datasets import load_dataset
import logging

def fine_tune_toxicity_model(dataset_name='toxic_dataset', model_name='xlm-roberta-base', output_dir='models/toxicity_model'):
    """Fine-tune a toxicity model on a specified dataset."""
    logging.info(f"Starting fine-tuning of {model_name} on {dataset_name}.")
    
    # Load dataset (e.g., from Hugging Face)
    dataset = load_dataset(dataset_name)
    tokenizer = XLMRobertaTokenizer.from_pretrained(model_name)
    model = XLMRobertaForSequenceClassification.from_pretrained(model_name, num_labels=2)

    # Tokenize dataset
    def tokenize_function(examples):
        return tokenizer(examples['text'], padding="max_length", truncation=True)

    tokenized_datasets = dataset.map(tokenize_function, batched=True)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
    )

    # Train and save
    trainer.train()
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    logging.info(f"Model fine-tuned and saved to {output_dir}.")

if __name__ == "__main__":
    # Example: fine_tune_toxicity_model(dataset_name="jigsaw_toxicity_pred", output_dir="models/custom_toxicity")
    fine_tune_toxicity_model()