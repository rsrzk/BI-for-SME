from flask import Blueprint, request, render_template, flash
from .g_drive_service import GoogleDriveService
from io import BytesIO
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
from apiclient import errors
from .models import User, Company
from . import db
from flask_login import login_required, current_user

driveapi = Blueprint('driveapi', __name__)

service = GoogleDriveService().build()

@driveapi.get('/all-files')
def get_all_files():
    selected_field="files(id, name, webViewLink, mimeType)"
    return service.files().list(fields=selected_field).execute()

@driveapi.get('/files-with-id/<file_id>/')
def get_files_with_id(file_id):
    selected_field="id, name, webViewLink, mimeType"
    return service.files().get(
        fileId=file_id,
        fields=selected_field
    ).execute()

@driveapi.get('/files-in-folder/<folder_id>/')
def get_files_in_folder(folder_id):
    selected_field="files(id, name, webViewLink, mimeType)"
    query=f" '{folder_id}' in parents "
    
    return service.files().list(
        q=query,
        fields=selected_field
    ).execute()

@driveapi.get('/files-with-type')
def get_files_with_type():
    selected_mimetype=request.json.get("mimetype")
    folder_mimeType = 'application/vnd.google-apps.folder'
    
    selected_field="files(id, name, webViewLink, mimeType)"
    
    query=f"mimeType != '{folder_mimeType}' and mimeType = '{selected_mimetype}'"
    
    return service.files().list(
        q=query,
        fields=selected_field
    ).execute()

@driveapi.get('/files-with-limit-offset-order')
def get_files_with_limit_offset_order():
    limit=request.args.get("limit")
    next_page_token=request.args.get("next_page_token")

    selected_field="nextPageToken, files(id, name, webViewLink, mimeType)"
    order_by="createdTime desc"
    
    result=service.files().list(
        pageSize=limit, 
        pageToken=next_page_token, 
        orderBy=order_by,
        fields=selected_field
    ).execute()
    return result

@driveapi.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    user = current_user
    company_name = user.company.company_name if user.company else None
    drive_folder = user.company.drive_folder if user.company else None
    if request.method == 'POST':
        uploaded_files = request.files.getlist("file")

        for uploaded_file in uploaded_files:
            buffer_memory = BytesIO()
            uploaded_file.save(buffer_memory)

            media_body = MediaIoBaseUpload(uploaded_file, uploaded_file.mimetype, resumable=True)

            created_at = datetime.now().strftime("%Y%m%d%H%M%S")

            file_metadata = {
                "name": f"{uploaded_file.filename} ({created_at})",
                "parents": [drive_folder]
            }

            returned_fields = "id, name, mimeType, webViewLink, exportLinks"

            upload_response = service.files().create(
                body=file_metadata,
                media_body=media_body,
                fields=returned_fields
            ).execute()

        flash('File uploaded successfully.', category='success')
        return render_template('upload.html', user=current_user, drive_folder=drive_folder, company_name=company_name)
    else:
        return render_template('upload.html', user=current_user, drive_folder=drive_folder, company_name=company_name)

@driveapi.delete('/file/<file_id>/')
def delete_file(file_id):
    try:
        service.files().delete(fileId=file_id).execute()
        return {"status":"OK"}
    except errors.HttpError as error:
        return {"status":"Fail", "error_message":error.reason}
    except Exception as e:
        return {"status":"Fail", "error_message":str(e)}