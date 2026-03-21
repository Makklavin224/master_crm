import { useState, useEffect } from "react";
import { Modal, InputNumber, Radio, Alert, App } from "antd";
import type { BookingRead } from "../api/bookings";
import { useServices } from "../api/services";
import { usePaymentSettings } from "../api/settings";
import {
  useCreateManualPayment,
  useCreateRobokassaPayment,
} from "../api/payments";

interface CompleteVisitModalProps {
  open: boolean;
  booking: BookingRead | null;
  onClose: () => void;
  onSuccess: () => void;
}

export function CompleteVisitModal({
  open,
  booking,
  onClose,
  onSuccess,
}: CompleteVisitModalProps) {
  const { message: messageApi } = App.useApp();
  const { data: services } = useServices();
  const { data: paymentSettings } = usePaymentSettings();
  const manualMutation = useCreateManualPayment();
  const robokassaMutation = useCreateRobokassaPayment();

  const [amount, setAmount] = useState<number>(0);
  const [paymentMethod, setPaymentMethod] = useState<
    "cash" | "card_to_card" | "sbp"
  >("cash");
  const [fiscalization, setFiscalization] = useState<
    "auto" | "manual" | "none"
  >("none");

  // Look up service price when booking or services change
  const servicePrice =
    services?.find((s) => s.id === booking?.service_id)?.price ?? 0;

  // Pre-fill amount and defaults when modal opens
  useEffect(() => {
    if (open && booking) {
      setAmount(servicePrice / 100);
      setPaymentMethod("cash");
      setFiscalization(
        (paymentSettings?.fiscalization_level as "auto" | "manual" | "none") ||
          "none",
      );
    }
  }, [open, booking, servicePrice, paymentSettings?.fiscalization_level]);

  const handleOk = async () => {
    if (!booking) return;

    const amountKopecks = Math.round(amount * 100);
    const amountOverride =
      amountKopecks !== servicePrice ? amountKopecks : undefined;

    try {
      if (paymentMethod === "sbp" && paymentSettings?.has_robokassa) {
        await robokassaMutation.mutateAsync({
          booking_id: booking.id,
          fiscalization_level: fiscalization,
          amount_override: amountOverride,
        });
      } else {
        await manualMutation.mutateAsync({
          booking_id: booking.id,
          payment_method: paymentMethod,
          fiscalization_level: fiscalization,
          amount_override: amountOverride,
        });
      }
      messageApi.success("Визит завершён, оплата принята");
      onSuccess();
    } catch {
      messageApi.error("Не удалось завершить визит");
    }
  };

  const isPending = manualMutation.isPending || robokassaMutation.isPending;

  return (
    <Modal
      title="Завершить визит"
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={isPending}
      okText="Завершить и принять оплату"
      cancelText="Отмена"
      okButtonProps={{ style: { background: "#00B894", borderColor: "#00B894" } }}
      destroyOnClose
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        {/* Amount */}
        <div>
          <div style={{ marginBottom: 6, fontWeight: 500 }}>Сумма</div>
          <InputNumber
            value={amount}
            onChange={(v) => setAmount(v ?? 0)}
            min={0}
            precision={0}
            addonAfter="&#8381;"
            style={{ width: "100%" }}
          />
        </div>

        {/* Payment method */}
        <div>
          <div style={{ marginBottom: 6, fontWeight: 500 }}>Способ оплаты</div>
          <Radio.Group
            value={paymentMethod}
            onChange={(e) => setPaymentMethod(e.target.value)}
            optionType="button"
            buttonStyle="solid"
          >
            <Radio.Button value="cash">Наличные</Radio.Button>
            <Radio.Button value="card_to_card">Перевод на карту</Radio.Button>
            {paymentSettings?.has_robokassa && (
              <Radio.Button value="sbp">СБП</Radio.Button>
            )}
          </Radio.Group>
        </div>

        {/* Fiscalization (only if Robokassa connected) */}
        {paymentSettings?.has_robokassa && (
          <div>
            <div style={{ marginBottom: 6, fontWeight: 500 }}>Чек</div>
            <Radio.Group
              value={fiscalization}
              onChange={(e) => setFiscalization(e.target.value)}
              optionType="button"
              buttonStyle="solid"
            >
              <Radio.Button value="auto">Авто</Radio.Button>
              <Radio.Button value="manual">Вручную</Radio.Button>
              <Radio.Button value="none">Без чека</Radio.Button>
            </Radio.Group>
            {fiscalization === "none" && (
              <Alert
                type="warning"
                message="Вы выбрали «Без чека». Чек не будет отправлен в ФНС."
                showIcon
                style={{ marginTop: 8 }}
              />
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}
