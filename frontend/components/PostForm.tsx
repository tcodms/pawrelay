"use client";

import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { ArrowRight, Camera } from "lucide-react";
import Spinner from "@/components/ui/Spinner";
import { getPhotoUploadUrl } from "@/lib/api/posts";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface PostFormValues {
  origin: string;
  destination: string;
  scheduled_date: string;
  animal_name: string;
  animal_size: "small" | "medium" | "large";
  animal_notes: string;
}

export interface PostFormInitialValues extends PostFormValues {
  animal_photo_url?: string;
}

interface PostFormProps {
  initialValues?: PostFormInitialValues;
  onSubmit: (values: PostFormValues, photoUrl: string) => Promise<void>;
  submitLabel: string;
}

// ── Styles ────────────────────────────────────────────────────────────────────

const INPUT_BASE =
  "h-12 w-full rounded-2xl border bg-white px-4 text-[14px] text-gray-700 placeholder:text-gray-400 shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-[#EEA968]/30";
const INPUT_NORMAL = `${INPUT_BASE} border-gray-200 focus:border-[#EEA968]/60`;
const INPUT_ERROR  = `${INPUT_BASE} border-red-300 bg-red-50 focus:border-red-400 focus:ring-red-100`;

const SIZE_OPTIONS: { value: "small" | "medium" | "large"; label: string; sub: string }[] = [
  { value: "small",  label: "소형", sub: "5kg 이하" },
  { value: "medium", label: "중형", sub: "15kg 이하" },
  { value: "large",  label: "대형", sub: "15kg 초과" },
];

// ── Component ─────────────────────────────────────────────────────────────────

export default function PostForm({ initialValues, onSubmit, submitLabel }: PostFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PostFormValues>({
    defaultValues: initialValues ?? {
      origin: "",
      destination: "",
      scheduled_date: "",
      animal_name: "",
      animal_size: "small",
      animal_notes: "",
    },
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [photoPreview, setPhotoPreview] = useState<string>(initialValues?.animal_photo_url ?? "");
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoError, setPhotoError] = useState("");

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
    setPhotoError("");
  }

  async function uploadPhoto(file: File): Promise<string> {
    // TODO: 실제 S3 업로드 플로우
    //   const { upload_url, photo_url } = await getPhotoUploadUrl(file.name);
    //   await fetch(upload_url, { method: "PUT", body: file, headers: { "Content-Type": file.type } });
    //   return photo_url;
    void getPhotoUploadUrl; // 미사용 경고 방지
    return photoPreview; // Mock: 로컬 미리보기 URL 반환
  }

  async function onFormSubmit(values: PostFormValues) {
    let photoUrl = initialValues?.animal_photo_url ?? "";
    if (photoFile) {
      photoUrl = await uploadPhoto(photoFile);
    }
    await onSubmit(values, photoUrl);
  }

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} noValidate className="flex flex-col gap-5">

      {/* 사진 업로드 */}
      <div className="flex flex-col items-center gap-2">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="relative flex h-24 w-24 items-center justify-center rounded-full bg-gray-100 overflow-hidden border-2 border-dashed border-gray-200 hover:border-[#EEA968]/60 transition-colors"
        >
          {photoPreview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={photoPreview} alt="미리보기" className="h-full w-full object-cover" />
          ) : (
            <div className="flex flex-col items-center gap-1 text-gray-400">
              <Camera size={22} />
              <span className="text-[10px]">사진 추가</span>
            </div>
          )}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleFileChange}
        />
        {photoError && <p className="text-[11px] text-red-500">{photoError}</p>}
        <p className="text-[11px] text-gray-400">동물 사진 (선택)</p>
      </div>

      {/* 이동 경로 */}
      <div className="rounded-3xl bg-white border border-gray-100 shadow-sm px-5 py-4 flex flex-col gap-3">
        <p className="text-[12px] font-semibold text-gray-400">이동 경로</p>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="origin" className="text-[13px] font-semibold text-gray-600">출발지</label>
          <input
            id="origin"
            placeholder="예: 광주광역시 북구"
            {...register("origin", { required: "출발지를 입력해 주세요." })}
            className={errors.origin ? INPUT_ERROR : INPUT_NORMAL}
          />
          {errors.origin && (
            <p role="alert" className="text-[11px] text-red-500">{errors.origin.message}</p>
          )}
        </div>

        <div className="flex justify-center">
          <ArrowRight size={16} className="text-gray-300" />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="destination" className="text-[13px] font-semibold text-gray-600">도착지</label>
          <input
            id="destination"
            placeholder="예: 서울특별시 강남구"
            {...register("destination", { required: "도착지를 입력해 주세요." })}
            className={errors.destination ? INPUT_ERROR : INPUT_NORMAL}
          />
          {errors.destination && (
            <p role="alert" className="text-[11px] text-red-500">{errors.destination.message}</p>
          )}
        </div>
      </div>

      {/* 이동 날짜 */}
      <div className="rounded-3xl bg-white border border-gray-100 shadow-sm px-5 py-4 flex flex-col gap-1.5">
        <label htmlFor="scheduled_date" className="text-[12px] font-semibold text-gray-400">이동 날짜</label>
        <input
          id="scheduled_date"
          type="date"
          {...register("scheduled_date", { required: "이동 날짜를 선택해 주세요." })}
          className={errors.scheduled_date ? INPUT_ERROR : INPUT_NORMAL}
        />
        {errors.scheduled_date && (
          <p role="alert" className="text-[11px] text-red-500">{errors.scheduled_date.message}</p>
        )}
      </div>

      {/* 동물 정보 */}
      <div className="rounded-3xl bg-white border border-gray-100 shadow-sm px-5 py-4 flex flex-col gap-4">
        <p className="text-[12px] font-semibold text-gray-400">동물 정보</p>

        {/* 이름 */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="animal_name" className="text-[13px] font-semibold text-gray-600">이름</label>
          <input
            id="animal_name"
            placeholder="예: 초코"
            {...register("animal_name", { required: "동물 이름을 입력해 주세요." })}
            className={errors.animal_name ? INPUT_ERROR : INPUT_NORMAL}
          />
          {errors.animal_name && (
            <p role="alert" className="text-[11px] text-red-500">{errors.animal_name.message}</p>
          )}
        </div>

        {/* 크기 */}
        <div className="flex flex-col gap-2">
          <p className="text-[13px] font-semibold text-gray-600">크기</p>
          <div className="grid grid-cols-3 gap-2">
            {SIZE_OPTIONS.map(({ value, label, sub }) => (
              <label
                key={value}
                className="flex flex-col items-center gap-0.5 cursor-pointer"
              >
                <input
                  type="radio"
                  value={value}
                  {...register("animal_size", { required: true })}
                  className="peer sr-only"
                />
                <div className="w-full flex flex-col items-center rounded-2xl border-2 border-gray-100 py-2.5 text-center transition-all peer-checked:border-[#EEA968] peer-checked:bg-[#FDF3EC]">
                  <span className="text-[13px] font-bold text-gray-700">{label}</span>
                  <span className="text-[10px] text-gray-400">{sub}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* 특이사항 */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="animal_notes" className="text-[13px] font-semibold text-gray-600">
            특이사항 <span className="text-gray-400 font-normal">(선택)</span>
          </label>
          <textarea
            id="animal_notes"
            rows={3}
            placeholder="예: 겁이 많아 조용한 이동이 필요해요."
            {...register("animal_notes")}
            className="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-700 placeholder:text-gray-400 shadow-sm resize-none focus:outline-none focus:border-[#EEA968]/60 focus:ring-2 focus:ring-[#EEA968]/30 transition-colors"
          />
        </div>
      </div>

      {/* 제출 버튼 */}
      <button
        type="submit"
        disabled={isSubmitting}
        className="h-14 w-full rounded-full bg-[#EEA968] text-[15px] font-bold text-white shadow-md shadow-[#EEA968]/20 transition-all active:scale-[0.97] hover:bg-[#D99A55] disabled:bg-gray-100 disabled:text-gray-400 disabled:shadow-none"
      >
        {isSubmitting ? (
          <span className="flex items-center justify-center gap-2.5">
            <Spinner />
            처리 중...
          </span>
        ) : submitLabel}
      </button>
    </form>
  );
}
