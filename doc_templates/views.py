import io
import json
from pathlib import Path

from django import forms
from django.shortcuts import render, reverse, redirect
from django.http import JsonResponse
from docxtpl import DocxTemplate
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload


DOCX_MIMETYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
CREDENTIALS_PATH = 'service-account-credentials.json'


class NewTemplateForm(forms.Form):
    template_id = forms.CharField(label='Template document id')
    preview_id = forms.CharField(label='Preview document id (will be overwritten)')


def new_template(request):
    credentials = json.loads(Path(CREDENTIALS_PATH).read_text('utf8'))
    if request.method == 'POST':
        form = NewTemplateForm(request.POST)
        if form.is_valid():
            return redirect(
                'preview_template',
                template_id=form.cleaned_data['template_id'],
                preview_id=form.cleaned_data['preview_id'],
            )
    else:
        form = NewTemplateForm()
    return render(request, 'doc_templates/new_template.html', {
        'share_email': credentials['client_email'],
        'form': form,
    })


def preview_template(request, template_id, preview_id):
    return render(request, 'doc_templates/preview_template.html', {
        'hide_iframes': bool(request.GET.get('hide_iframes')),
        'template_doc_url': get_document_url(template_id),
        'preview_doc_url': get_document_url(preview_id),
        'refresh_url': reverse(
            'refresh_target', kwargs=dict(
                template_id=template_id,
                preview_id=preview_id,
            ),
        ),
    })


def render_target(source_id: str, target_id: str):
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/drive'],
    )
    drive = build('drive', 'v3', credentials=credentials)
    template = download_docx(drive, source_id)
    doc = DocxTemplate(io.BytesIO(template))
    context = {
        'name' : 'Костя',
        'условие': True,
    }
    doc.render(context)
    out_f = io.BytesIO()
    doc.save(out_f)
    upload_docx(drive, target_id, out_f.getvalue())


def download_docx(drive, doc_id: str) -> bytes:
    request = drive.files().export_media(fileId=doc_id, mimeType=DOCX_MIMETYPE)
    f = io.BytesIO()
    downloader = MediaIoBaseDownload(f, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    return f.getvalue()


def upload_docx(drive, doc_id: str, body: bytes):
    drive.files().update(
        fileId=doc_id,
        media_body=MediaIoBaseUpload(io.BytesIO(body), mimetype=DOCX_MIMETYPE),
    ).execute()


def refresh_target(request, template_id, preview_id):
    render_target(template_id, preview_id)
    result = {}
    return JsonResponse(result)


def get_document_url(doc_id: str) -> str:
    return f'https://docs.google.com/document/d/{doc_id}/edit'
