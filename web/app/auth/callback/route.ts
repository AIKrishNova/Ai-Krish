import { NextResponse, type NextRequest } from "next/server";
import type { EmailOtpType } from "@supabase/supabase-js";
import { createClient } from "../../../lib/supabase/server";
import { safeNext } from "../../../lib/authValidation";

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url);
  const next = safeNext(searchParams.get("next"));
  const recovery = next.startsWith("/reset-password");
  const fail = (status: string) =>
    NextResponse.redirect(origin + (recovery ? `/forgot-password?status=${status}` : `/verify?status=${status}`));

  if (searchParams.get("error_code") || searchParams.get("error")) {
    return fail(searchParams.get("error_code") === "otp_expired" ? "expired" : "invalid");
  }

  const supabase = await createClient();
  const code = searchParams.get("code");
  const tokenHash = searchParams.get("token_hash");
  const type = searchParams.get("type") as EmailOtpType | null;
  let failed = false;
  try {
    if (code) failed = !!(await supabase.auth.exchangeCodeForSession(code)).error;
    else if (tokenHash && type) failed = !!(await supabase.auth.verifyOtp({ type, token_hash: tokenHash })).error;
    else failed = true;
  } catch {
    failed = true;
  }
  if (failed) return fail("invalid");
  return NextResponse.redirect(origin + (next === "/" ? "/verify?status=verified" : next));
}
