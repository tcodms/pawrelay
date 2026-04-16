"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Camera, X } from "lucide-react";
import Spinner from "@/components/ui/Spinner";
import { createPost, getPhotoUploadUrl } from "@/lib/api/posts";

// ── 스타일 상수 ───────────────────────────────────────────────────────────────

const INPUT_BASE =
  "h-12 w-full rounded-2xl border bg-white px-4 text-[14px] text-gray-700 placeholder:text-gray-400 shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-[#EEA968]/20 focus:border-[#EEA968]/60";
const INPUT_NORMAL = `${INPUT_BASE} border-gray-200`;
const INPUT_ERROR  = `${INPUT_BASE} border-red-300 bg-red-50`;

const SIZE_OPTIONS = [
  { value: "small",  label: "소형", sub: "5kg 이하" },
  { value: "medium", label: "중형", sub: "15kg 이하" },
  { value: "large",  label: "대형", sub: "15kg 초과" },
] as const;

type AnimalSize = "small" | "medium" | "large";

// ── 유효성 검사 ───────────────────────────────────────────────────────────────

interface FormErrors {
  origin?: string;
  destination?: string;
  scheduled_date?: string;
  animal_name?: string;
}

function validate(fields: {
  origin: string;
  destination: string;
  scheduled_date: string;
  animal_name: string;
}): FormErrors {
  const errors: FormErrors = {};
  if (!fields.origin.trim())        errors.origin = "출발지를 입력해 주세요.";
  if (!fields.destination.trim())   errors.destination = "도착지를 입력해 주세요.";
  if (!fields.scheduled_date)       errors.scheduled_date = "이동 날짜를 선택해 주세요.";
  if (!fields.animal_name.trim())   errors.animal_name = "동물 이름을 입력해 주세요.";
  return errors;
}

// ── 페이지 ────────────────────────────────────────────────────────────────────

export default function NewPostPage() {
  const router = useRouter();

  const [origin, setOrigin]               = useState("");
  const [destination, setDestination]     = useState("");
  const [scheduledDate, setScheduledDate] = useState("");
  const [animalName, setAnimalName]       = useState("");
  const [animalSize, setAnimalSize]       = useState<AnimalSize>("small");
  const [animalNotes, setAnimalNotes]     = useState("");

  const [photoPreview, setPhotoPreview] = useState<string>("");
  const [photoFile, setPhotoFile]       = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [errors, setErrors]   = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
  }

  async function uploadPhoto(file: File): Promise<string> {
    // TODO: 실제 S3 업로드 플로우
    // const { upload_url, photo_url } = await getPhotoUploadUrl(file.name);
    // await fetch(upload_url, { method: "PUT", body: file, headers: { "Content-Type": file.type } });
    // return photo_url;
    void getPhotoUploadUrl;
    return URL.createObjectURL(file); // Mock
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const fieldErrors = validate({ origin, destination, scheduled_date: scheduledDate, animal_name: animalName });
    if (Object.keys(fieldErrors).length > 0) {
      setErrors(fieldErrors);
      return;
    }
    setLoading(true);
    try {
      let photoUrl: string | undefined;
      if (photoFile) photoUrl = await uploadPhoto(photoFile);

      await createPost({
        origin,
        destination,
        scheduled_date: scheduledDate,
        animal_info: {
          name:      animalName,
          size:      animalSize,
          photo_url: photoUrl,
          notes:     animalNotes.trim() || undefined,
        },
      });
      router.push("/dashboard");
    } catch {
      alert("공고 등록에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50">

      {/* 헤더 */}
      <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-gray-100 bg-white/90 px-4 py-4 backdrop-blur-sm">
        <Link
          href="/dashboard"
          aria-label="뒤로 가기"
          className="flex h-9 w-9 items-center justify-center rounded-xl text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft size={20} />
        </Link>
        <h1 className="flex-1 text-[17px] font-bold text-gray-900">새 공고 등록</h1>
      </header>

      <form onSubmit={handleSubmit} noValidate>
        <div className="mx-auto max-w-lg px-4 py-6 flex flex-col gap-4">

          {/* 사진 업로드 */}
          <div className="flex flex-col items-center gap-2">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="relative flex h-24 w-24 items-center justify-center rounded-full overflow-hidden border-2 border-dashed border-gray-200 bg-gray-50 hover:border-[#EEA968]/60 transition-colors"
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
            {photoPreview && (
              <button
                type="button"
                onClick={() => { setPhotoPreview(""); setPhotoFile(null); }}
                className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-red-400 transition-colors"
              >
                <X size={11} />
                사진 제거
              </button>
            )}
            <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
            <p className="text-[11px] text-gray-400">동물 사진 (선택)</p>
          </div>

          {/* 이동 정보 */}
          <div className="rounded-3xl bg-white border border-gray-100 shadow-sm px-5 py-5 flex flex-col gap-4">
            <p className="text-[12px] font-semibold text-gray-400 uppercase tracking-wide">이동 정보</p>

            {/* 출발지 */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="origin" className="text-[13px] font-semibold text-gray-600">출발지</label>
              <input
                id="origin"
                value={origin}
                onChange={(e) => { setOrigin(e.target.value); setErrors((p) => ({ ...p, origin: undefined })); }}
                placeholder="예: 광주광역시 북구"
                className={errors.origin ? INPUT_ERROR : INPUT_NORMAL}
              />
              {errors.origin && <p role="alert" className="text-[11px] text-red-500">{errors.origin}</p>}
            </div>

            {/* 도착지 */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="destination" className="text-[13px] font-semibold text-gray-600">도착지</label>
              <input
                id="destination"
                value={destination}
                onChange={(e) => { setDestination(e.target.value); setErrors((p) => ({ ...p, destination: undefined })); }}
                placeholder="예: 서울특별시 강남구"
                className={errors.destination ? INPUT_ERROR : INPUT_NORMAL}
              />
              {errors.destination && <p role="alert" className="text-[11px] text-red-500">{errors.destination}</p>}
            </div>

            {/* 이동 날짜 */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="scheduled_date" className="text-[13px] font-semibold text-gray-600">이동 날짜</label>
              <input
                id="scheduled_date"
                type="date"
                value={scheduledDate}
                onChange={(e) => { setScheduledDate(e.target.value); setErrors((p) => ({ ...p, scheduled_date: undefined })); }}
                className={errors.scheduled_date ? INPUT_ERROR : INPUT_NORMAL}
              />
              {errors.scheduled_date && <p role="alert" className="text-[11px] text-red-500">{errors.scheduled_date}</p>}
            </div>
          </div>

          {/* 동물 정보 */}
          <div className="rounded-3xl bg-white border border-gray-100 shadow-sm px-5 py-5 flex flex-col gap-4">
            <p className="text-[12px] font-semibold text-gray-400 uppercase tracking-wide">동물 정보</p>

            {/* 이름 */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="animal_name" className="text-[13px] font-semibold text-gray-600">이름</label>
              <input
                id="animal_name"
                value={animalName}
                onChange={(e) => { setAnimalName(e.target.value); setErrors((p) => ({ ...p, animal_name: undefined })); }}
                placeholder="예: 초코"
                className={errors.animal_name ? INPUT_ERROR : INPUT_NORMAL}
              />
              {errors.animal_name && <p role="alert" className="text-[11px] text-red-500">{errors.animal_name}</p>}
            </div>

            {/* 크기 */}
            <div className="flex flex-col gap-2">
              <p className="text-[13px] font-semibold text-gray-600">크기</p>
              <div className="grid grid-cols-3 gap-2">
                {SIZE_OPTIONS.map(({ value, label, sub }) => (
                  <label key={value} className="cursor-pointer">
                    <input
                      type="radio"
                      name="animal_size"
                      value={value}
                      checked={animalSize === value}
                      onChange={() => setAnimalSize(value)}
                      className="sr-only"
                    />
                    <div className={`flex flex-col items-center rounded-2xl border-2 py-3 text-center transition-all ${
                      animalSize === value
                        ? "border-[#EEA968] bg-[#FDF3EC]"
                        : "border-gray-100 bg-gray-50 hover:border-gray-200"
                    }`}>
                      <span className="text-[13px] font-bold text-gray-700">{label}</span>
                      <span className="text-[10px] text-gray-400 mt-0.5">{sub}</span>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* 기타 참고사항 */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="animal_notes" className="text-[13px] font-semibold text-gray-600">
                기타 참고사항 <span className="font-normal text-gray-400">(선택)</span>
              </label>
              <textarea
                id="animal_notes"
                rows={3}
                value={animalNotes}
                onChange={(e) => setAnimalNotes(e.target.value)}
                placeholder="예: 겁이 많아 조용한 이동이 필요해요."
                className="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-[14px] text-gray-700 placeholder:text-gray-400 shadow-sm resize-none focus:outline-none focus:ring-2 focus:ring-[#EEA968]/20 focus:border-[#EEA968]/60 transition-colors"
              />
            </div>
          </div>

          {/* 제출 버튼 */}
          <button
            type="submit"
            disabled={loading}
            className="h-14 w-full rounded-full bg-[#EEA968] text-[15px] font-bold text-white shadow-md shadow-[#EEA968]/20 transition-all active:scale-[0.97] hover:bg-[#D99A55] disabled:bg-gray-100 disabled:text-gray-400 disabled:shadow-none"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2.5">
                <Spinner />
                등록 중...
              </span>
            ) : "공고 등록하기"}
          </button>

        </div>
      </form>
    </main>
  );
}
