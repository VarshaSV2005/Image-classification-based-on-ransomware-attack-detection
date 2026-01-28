print(f"Training complete. Best validation accuracy: {best_val_acc:.4f}")

# Save training metrics for web app display
metrics_path = os.path.join('model', 'training_metrics.json')
import json
metrics = {
    'best_validation_accuracy': float(best_val_acc),
    'training_accuracy': float(train_acc),
    'validation_accuracy': float(val_acc),
    'training_loss': float(train_loss) if 'train_loss' in locals() else 0.0,
    'validation_loss': float(val_loss) if 'val_loss' in locals() else 0.0,
        'epochs_completed': epochs,
        'model_path': MODEL_PATH
    }

    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Training metrics saved to {metrics_path}")

    # Print classification report
    if all_preds and all_labels:
        print("\nClassification Report:")
        print(classification_report(all_labels, all_preds, target_names=['Benign', 'Ransomware']))
