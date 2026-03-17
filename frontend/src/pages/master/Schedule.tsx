import { useState, useEffect } from "react";
import { Plus, Trash2 } from "lucide-react";
import {
  useMasterSchedule,
  useUpdateSchedule,
  useScheduleExceptions,
  useCreateException,
  useDeleteException,
  type ScheduleDayRead,
  type ScheduleExceptionCreate,
} from "../../api/master-schedule.ts";
import { Card } from "../../components/ui/Card.tsx";
import { Input } from "../../components/ui/Input.tsx";
import { Button } from "../../components/ui/Button.tsx";
import { Skeleton } from "../../components/ui/Skeleton.tsx";
import { ConfirmDialog } from "../../components/ConfirmDialog.tsx";
import { useToast } from "../../components/ui/Toast.tsx";
import { formatDate } from "../../lib/format.ts";

const DAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

const DEFAULT_SCHEDULE: ScheduleDayRead[] = Array.from({ length: 7 }, (_, i) => ({
  day_of_week: i,
  start_time: i < 5 ? "09:00" : null,
  end_time: i < 5 ? "18:00" : null,
  break_start: null,
  break_end: null,
  is_working: i < 5,
}));

export function Schedule() {
  const { data: scheduleData, isLoading: scheduleLoading } = useMasterSchedule();
  const { data: exceptions, isLoading: exceptionsLoading } = useScheduleExceptions();
  const updateSchedule = useUpdateSchedule();
  const createException = useCreateException();
  const deleteException = useDeleteException();
  const toast = useToast();

  const [days, setDays] = useState<ScheduleDayRead[]>(DEFAULT_SCHEDULE);
  const [showAddException, setShowAddException] = useState(false);
  const [newException, setNewException] = useState<ScheduleExceptionCreate>({
    exception_date: "",
    is_day_off: true,
    start_time: null,
    end_time: null,
    reason: null,
  });
  const [deleteExId, setDeleteExId] = useState<string | null>(null);

  useEffect(() => {
    if (scheduleData && scheduleData.length > 0) {
      setDays(scheduleData);
    }
  }, [scheduleData]);

  const updateDay = (index: number, updates: Partial<ScheduleDayRead>) => {
    setDays((prev) =>
      prev.map((d, i) => (i === index ? { ...d, ...updates } : d)),
    );
  };

  const handleSaveSchedule = () => {
    updateSchedule.mutate(
      { days },
      {
        onSuccess: () => toast.success("Расписание сохранено"),
        onError: () => toast.error("Не удалось сохранить расписание"),
      },
    );
  };

  const handleAddException = () => {
    if (!newException.exception_date) {
      toast.error("Выберите дату");
      return;
    }
    createException.mutate(newException, {
      onSuccess: () => {
        toast.success("Исключение добавлено");
        setShowAddException(false);
        setNewException({
          exception_date: "",
          is_day_off: true,
          start_time: null,
          end_time: null,
          reason: null,
        });
      },
      onError: () => toast.error("Не удалось добавить исключение"),
    });
  };

  const handleDeleteException = () => {
    if (!deleteExId) return;
    deleteException.mutate(deleteExId, {
      onSuccess: () => {
        toast.success("Исключение удалено");
        setDeleteExId(null);
      },
      onError: () => toast.error("Не удалось удалить"),
    });
  };

  const isLoading = scheduleLoading || exceptionsLoading;

  return (
    <div className="flex flex-col min-h-full">
      <div className="px-4 pt-8 pb-4">
        <h1 className="text-[20px] font-semibold text-text-primary">
          Расписание
        </h1>
      </div>

      <div className="flex-1 px-4 pb-4 flex flex-col gap-4">
        {isLoading ? (
          <div className="flex flex-col gap-3">
            {[1, 2, 3, 4, 5, 6, 7].map((i) => (
              <Skeleton key={i} height="56px" className="w-full" />
            ))}
          </div>
        ) : (
          <>
            {/* Weekly schedule */}
            <div className="flex flex-col gap-3">
              {days.map((day, index) => (
                <Card key={day.day_of_week} className="flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[16px] font-semibold text-text-primary w-8">
                      {DAY_NAMES[index]}
                    </span>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <span className="text-[12px] text-text-secondary">
                        {day.is_working ? "Рабочий" : "Выходной"}
                      </span>
                      <input
                        type="checkbox"
                        checked={day.is_working}
                        onChange={(e) =>
                          updateDay(index, { is_working: e.target.checked })
                        }
                        className="w-5 h-5 accent-accent rounded"
                      />
                    </label>
                  </div>

                  {day.is_working && (
                    <>
                      <div className="flex items-center gap-2">
                        <input
                          type="time"
                          value={day.start_time || "09:00"}
                          onChange={(e) =>
                            updateDay(index, { start_time: e.target.value })
                          }
                          className="h-[44px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary flex-1 outline-none focus:ring-2 focus:ring-accent/30"
                        />
                        <span className="text-text-secondary text-[14px]">—</span>
                        <input
                          type="time"
                          value={day.end_time || "18:00"}
                          onChange={(e) =>
                            updateDay(index, { end_time: e.target.value })
                          }
                          className="h-[44px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary flex-1 outline-none focus:ring-2 focus:ring-accent/30"
                        />
                      </div>

                      {/* Break toggle */}
                      <div className="flex flex-col gap-2">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={!!day.break_start}
                            onChange={(e) =>
                              updateDay(index, {
                                break_start: e.target.checked ? "13:00" : null,
                                break_end: e.target.checked ? "14:00" : null,
                              })
                            }
                            className="w-4 h-4 accent-accent rounded"
                          />
                          <span className="text-[12px] text-text-secondary">
                            Перерыв
                          </span>
                        </label>
                        {day.break_start && (
                          <div className="flex items-center gap-2 pl-6">
                            <input
                              type="time"
                              value={day.break_start}
                              onChange={(e) =>
                                updateDay(index, { break_start: e.target.value })
                              }
                              className="h-[40px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary flex-1 outline-none focus:ring-2 focus:ring-accent/30"
                            />
                            <span className="text-text-secondary text-[14px]">—</span>
                            <input
                              type="time"
                              value={day.break_end || "14:00"}
                              onChange={(e) =>
                                updateDay(index, { break_end: e.target.value })
                              }
                              className="h-[40px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary flex-1 outline-none focus:ring-2 focus:ring-accent/30"
                            />
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </Card>
              ))}
            </div>

            <Button
              onClick={handleSaveSchedule}
              loading={updateSchedule.isPending}
              fullWidth
            >
              Сохранить настройки
            </Button>

            {/* Exceptions section */}
            <div className="mt-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-[16px] font-semibold text-text-primary">
                  Исключения
                </h2>
                <button
                  onClick={() => setShowAddException(true)}
                  className="w-10 h-10 flex items-center justify-center rounded-full text-accent hover:bg-surface transition-colors"
                  aria-label="Добавить исключение"
                >
                  <Plus className="w-6 h-6" />
                </button>
              </div>

              {exceptions && exceptions.length > 0 ? (
                <div className="flex flex-col gap-3">
                  {exceptions.map((ex) => (
                    <Card
                      key={ex.id}
                      className="flex items-center justify-between"
                    >
                      <div>
                        <div className="text-[14px] font-semibold text-text-primary">
                          {formatDate(ex.exception_date)}
                        </div>
                        <div className="text-[12px] text-text-secondary">
                          {ex.is_day_off
                            ? "Выходной"
                            : `${ex.start_time} — ${ex.end_time}`}
                          {ex.reason && ` · ${ex.reason}`}
                        </div>
                      </div>
                      <button
                        onClick={() => setDeleteExId(ex.id)}
                        className="w-8 h-8 flex items-center justify-center rounded-full text-destructive hover:bg-red-50 transition-colors"
                        aria-label="Удалить исключение"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </Card>
                  ))}
                </div>
              ) : (
                <p className="text-[14px] text-text-secondary text-center py-4">
                  Нет исключений
                </p>
              )}
            </div>

            {/* Add exception form */}
            {showAddException && (
              <Card className="flex flex-col gap-3 mt-2">
                <h3 className="text-[16px] font-semibold text-text-primary">
                  Новое исключение
                </h3>
                <Input
                  label="Дата"
                  type="date"
                  value={newException.exception_date}
                  onChange={(e) =>
                    setNewException((prev) => ({
                      ...prev,
                      exception_date: e.target.value,
                    }))
                  }
                />
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newException.is_day_off}
                    onChange={(e) =>
                      setNewException((prev) => ({
                        ...prev,
                        is_day_off: e.target.checked,
                        start_time: e.target.checked ? null : "09:00",
                        end_time: e.target.checked ? null : "18:00",
                      }))
                    }
                    className="w-4 h-4 accent-accent rounded"
                  />
                  <span className="text-[14px] text-text-primary">Выходной</span>
                </label>
                {!newException.is_day_off && (
                  <div className="flex items-center gap-2">
                    <input
                      type="time"
                      value={newException.start_time || "09:00"}
                      onChange={(e) =>
                        setNewException((prev) => ({
                          ...prev,
                          start_time: e.target.value,
                        }))
                      }
                      className="h-[44px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary flex-1 outline-none focus:ring-2 focus:ring-accent/30"
                    />
                    <span className="text-text-secondary">—</span>
                    <input
                      type="time"
                      value={newException.end_time || "18:00"}
                      onChange={(e) =>
                        setNewException((prev) => ({
                          ...prev,
                          end_time: e.target.value,
                        }))
                      }
                      className="h-[44px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary flex-1 outline-none focus:ring-2 focus:ring-accent/30"
                    />
                  </div>
                )}
                <Input
                  label="Причина"
                  placeholder="Отпуск, праздник..."
                  value={newException.reason || ""}
                  onChange={(e) =>
                    setNewException((prev) => ({
                      ...prev,
                      reason: e.target.value || null,
                    }))
                  }
                />
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    onClick={() => setShowAddException(false)}
                    fullWidth
                  >
                    Отмена
                  </Button>
                  <Button
                    onClick={handleAddException}
                    loading={createException.isPending}
                    fullWidth
                  >
                    Добавить
                  </Button>
                </div>
              </Card>
            )}
          </>
        )}
      </div>

      <ConfirmDialog
        isOpen={!!deleteExId}
        title="Удалить исключение?"
        message="Удалить это исключение из расписания?"
        confirmLabel="Удалить"
        cancelLabel="Не удалять"
        variant="destructive"
        onConfirm={handleDeleteException}
        onCancel={() => setDeleteExId(null)}
      />
    </div>
  );
}
