import Button from "./Button.jsx";
import Modal from "./Modal.jsx";

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  tone = "primary",
  onConfirm,
  onCancel,
}) {
  return (
    <Modal open={open} title={title} onClose={onCancel}>
      <div className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed font-normal">{message}</div>
      <div className="mt-6 flex justify-end gap-2.5">
        <Button variant="subtle" size="sm" onClick={onCancel}>
          Cancel
        </Button>
        <Button variant={tone} size="sm" onClick={onConfirm}>
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}
