from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from auth import require_hr
import models
import schemas

router = APIRouter(prefix="/admin", tags=["Admin"])

# NOTE ON RESPONSIBILITIES:
# The actual PDF ingestion (chunking + embeddings + writing to ChromaDB) happens
# in the MCP server (mcp_server/rag/ingest.py), because that's where the vector
# DB and embedding model live. This router only stores/reads *metadata* about
# ingested documents (filename, who uploaded it, chunk count, vector ids) so the
# HR admin dashboard can list/delete documents without talking to the vector DB
# directly. The MCP server calls these endpoints right after it ingests or
# deletes a document, using the HR user's own JWT.


@router.get("/documents", response_model=List[schemas.HRDocumentOut])
def list_hr_documents(db: Session = Depends(get_db), current=Depends(require_hr)):
    return db.query(models.HRDocument).order_by(models.HRDocument.uploaded_at.desc()).all()


@router.post("/documents", response_model=schemas.HRDocumentOut, status_code=201)
def register_hr_document(
    file_name: str,
    original_name: str,
    chunk_count: int,
    vector_ids: str,
    db: Session = Depends(get_db),
    current=Depends(require_hr),
):
    """Called by the MCP server right after it ingests a PDF into the vector DB."""
    doc = models.HRDocument(
        file_name=file_name,
        original_name=original_name,
        uploaded_by=current.employee_id,
        chunk_count=chunk_count,
        vector_ids=vector_ids,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/documents/{doc_id}")
def delete_hr_document_metadata(
    doc_id: int, db: Session = Depends(get_db), current=Depends(require_hr)
):
    """
    Deletes only the metadata row. The frontend should call the MCP server's
    /admin/documents/{doc_id}/delete FIRST (to remove vectors from ChromaDB),
    which in turn calls this endpoint to clean up metadata. See mcp_server/server.py.
    """
    doc = db.query(models.HRDocument).filter(models.HRDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"detail": "Deleted"}
