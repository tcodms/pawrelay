"use client";

import { useEffect, useRef, useState } from "react";

declare global {
  interface Window {
    kakao: any;
  }
}

export interface LatLng {
  latitude: number;
  longitude: number;
}

export type MarkerType = "departure" | "arrival" | "checkpoint";

export interface MapMarker extends LatLng {
  type: MarkerType;
}

interface KakaoMapProps {
  latitude?: number;
  longitude?: number;
  level?: number;
  className?: string;
  markers?: MapMarker[];
  polyline?: LatLng[];
}

const MARKER_COLORS: Record<MarkerType, string> = {
  departure:  "#22c55e",
  arrival:    "#ef4444",
  checkpoint: "#3b82f6",
};

function makeMarkerImage(type: MarkerType) {
  const color = MARKER_COLORS[type];
  const size = 14;
  const radius = size / 2 - 1;
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}">` +
    `<circle cx="${size / 2}" cy="${size / 2}" r="${radius}" fill="${color}" stroke="white" stroke-width="2"/>` +
    `</svg>`;
  return new window.kakao.maps.MarkerImage(
    `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`,
    new window.kakao.maps.Size(size, size),
    { offset: new window.kakao.maps.Point(size / 2, size / 2) },
  );
}

function renderMarkers(map: any, markers: MapMarker[], existing: any[]): any[] {
  existing.forEach((m) => m.setMap(null));
  if (!markers.length) return [];

  const bounds = new window.kakao.maps.LatLngBounds();
  const created = markers.map(({ latitude: lat, longitude: lng, type }) => {
    const position = new window.kakao.maps.LatLng(lat, lng);
    bounds.extend(position);
    return new window.kakao.maps.Marker({ map, position, image: makeMarkerImage(type) });
  });
  map.setBounds(bounds);
  return created;
}

function renderPolyline(map: any, path: LatLng[], existing: any | null): any | null {
  if (existing) existing.setMap(null);
  if (!path.length) return null;

  return new window.kakao.maps.Polyline({
    map,
    path: path.map(({ latitude: lat, longitude: lng }) =>
      new window.kakao.maps.LatLng(lat, lng)
    ),
    strokeWeight: 4,
    strokeColor: "#6366f1",
    strokeOpacity: 0.8,
    strokeStyle: "solid",
  });
}

export default function KakaoMap({
  latitude = 37.5665,
  longitude = 126.978,
  level = 5,
  className = "w-full h-[400px]",
  markers,
  polyline,
}: KakaoMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const kakaoMarkersRef = useRef<any[]>([]);
  const kakaoPolylineRef = useRef<any>(null);

  const [mapState, setMapState] = useState<"loading" | "ready" | "no-key" | "error">("loading");

  useEffect(() => {
    const apiKey = process.env.NEXT_PUBLIC_KAKAO_MAP_API_KEY;
    if (!apiKey || apiKey.startsWith("your_")) {
      setMapState("no-key");
      return;
    }

    function initMap() {
      window.kakao.maps.load(() => {
        if (!containerRef.current) return;
        mapRef.current = new window.kakao.maps.Map(containerRef.current, {
          center: new window.kakao.maps.LatLng(latitude, longitude),
          level,
        });
        setMapState("ready");
      });
    }

    // SDK가 이미 로드된 경우 (React strict mode 두 번째 실행 등)
    if (window.kakao?.maps) {
      initMap();
      return;
    }

    // 스크립트 태그가 이미 DOM에 있는 경우 (중복 삽입 방지)
    const existing = document.querySelector(`script[src*="dapi.kakao.com/v2/maps"]`);
    if (existing) {
      existing.addEventListener("load", initMap);
      return () => existing.removeEventListener("load", initMap);
    }

    const script = document.createElement("script");
    script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${apiKey}&autoload=false`;
    script.async = true;
    script.onload = initMap;
    script.onerror = () => setMapState("error");
    document.head.appendChild(script);

    // 스크립트는 제거하지 않음 — cleanup에서 제거하면 로딩 중 onerror 트리거됨
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;
    const center = new window.kakao.maps.LatLng(latitude, longitude);
    mapRef.current.setCenter(center);
  }, [latitude, longitude]);

  useEffect(() => {
    if (mapState !== "ready") return;
    kakaoMarkersRef.current = renderMarkers(mapRef.current, markers ?? [], kakaoMarkersRef.current);
  }, [markers, mapState]);

  useEffect(() => {
    if (mapState !== "ready") return;
    kakaoPolylineRef.current = renderPolyline(mapRef.current, polyline ?? [], kakaoPolylineRef.current);
  }, [polyline, mapState]);

  if (mapState === "no-key") {
    return (
      <div className={`${className} flex flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-orange-200 bg-orange-50`}>
        <span className="text-2xl">🗺️</span>
        <p className="text-[13px] font-semibold text-orange-500">.env.local에 카카오맵 API 키를 입력해 주세요</p>
        <p className="text-[11px] text-gray-400">NEXT_PUBLIC_KAKAO_MAP_API_KEY</p>
      </div>
    );
  }

  if (mapState === "error") {
    return (
      <div className={`${className} flex flex-col items-center justify-center gap-2 rounded-2xl border border-red-200 bg-red-50`}>
        <p className="text-[13px] font-semibold text-red-500">지도를 불러오지 못했습니다</p>
        <p className="text-[11px] text-gray-400">카카오 개발자 콘솔에서 도메인(localhost:3000)이 등록되었는지 확인하세요</p>
      </div>
    );
  }

  return (
    <div className={`${className} relative`}>
      {/* 지도가 그려질 컨테이너 — 항상 DOM에 존재해야 카카오 SDK가 참조 가능 */}
      <div
        ref={containerRef}
        className="absolute inset-0"
        aria-label="카카오 지도"
      />
      {/* 로딩 오버레이 */}
      {mapState === "loading" && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-2xl">
          <p className="text-[13px] text-gray-400">지도 불러오는 중...</p>
        </div>
      )}
    </div>
  );
}
