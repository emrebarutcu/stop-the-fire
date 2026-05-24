interface Props {
  message: string;
  detail?: string;
}

export default function LoadingOverlay({ message, detail }: Props) {
  return (
    <div className="loading-overlay">
      <div className="spinner" />
      <div className="msg">{message}</div>
      {detail && <div className="sub">{detail}</div>}
    </div>
  );
}
