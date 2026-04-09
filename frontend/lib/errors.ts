const ERROR_MESSAGES: Record<string, string> = {
  EMAIL_ALREADY_EXISTS: "이미 사용 중인 이메일입니다.",
  WEAK_PASSWORD: "비밀번호가 너무 약합니다. 영문+숫자+특수문자를 포함해 주세요.",
  INVALID_CREDENTIALS: "이메일 또는 비밀번호가 올바르지 않습니다.",
  ACCOUNT_SUSPENDED: "정지된 계정입니다. 관리자에게 문의하세요.",
  EMAIL_NOT_VERIFIED: "이메일 인증이 필요합니다. 메일함을 확인해 주세요.",
  INVALID_BUSINESS_NUMBER: "사업자번호는 10자리 숫자여야 합니다.",
  REFRESH_TOKEN_EXPIRED: "세션이 만료되었습니다. 다시 로그인해 주세요.",
  UNKNOWN_ERROR: "알 수 없는 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
};

export function getErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] ?? ERROR_MESSAGES.UNKNOWN_ERROR;
}
