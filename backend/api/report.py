# backend/api/report.py

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
import io
import csv
import traceback
from weasyprint import HTML

from ..services.supabase_client import supabase
from ..deps import get_current_user, User
from ..jinja_env import templates

router = APIRouter(prefix="/report", tags=["report"])

@router.get("")
async def view_report(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    try:
        status_resp = await supabase.rpc(
            "compute_ce_status", {"user_id": current_user.id}
        ).single().execute()
        status = status_resp.data or {}

        records_resp = await supabase.table("ce_records") \
            .select("course_title,date_completed,hours,notes") \
            .eq("user_id", current_user.id) \
            .execute()
        records = records_resp.data or []

        return templates.TemplateResponse(
            "report.html",
            {"request": request, "records": records, "status": status}
        )
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to load report page")


@router.get("/download_csv")
async def download_csv(current_user: User = Depends(get_current_user)):
    try:
        records_resp = await supabase.table("ce_records") \
            .select("course_title,date_completed,hours,notes") \
            .eq("user_id", current_user.id) \
            .execute()
        records = records_resp.data or []

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Course", "Date Completed", "Hours", "Notes"])
        for r in records:
            writer.writerow([
                r.get("course_title", ""),
                r.get("date_completed", ""),
                r.get("hours", ""),
                r.get("notes", ""),
            ])
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=ce_records.csv"}
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"CSV export failed: {e}")


@router.get("/download_pdf")
async def download_pdf(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_pro:
        raise HTTPException(status_code=403, detail="Upgrade to Pro to export PDF")

    try:
        records_resp = await supabase.table("ce_records") \
            .select("course_title,date_completed,hours,notes") \
            .eq("user_id", current_user.id) \
            .execute()
        records = records_resp.data or []

        status_resp = await supabase.rpc(
            "compute_ce_status", {"user_id": current_user.id}
        ).single().execute()
        status = status_resp.data or {}

        html_content = templates.get_template("report.html").render(
            request=request, records=records, status=status
        )
        pdf_bytes = HTML(string=html_content).write_pdf()

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=ce_report.pdf"}
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
