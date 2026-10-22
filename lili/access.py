"""Project authorization. Identity must come from a trusted server-side resolver.

This module never authenticates a user from a browser-provided ID/header. The
legacy deployment remains unchanged until the portal identity bridge is ready.
"""
import copy
import re
from dataclasses import dataclass
from .core import EditorError

PERMISSIONS=frozenset(("view","edit","download_exports","download_sources"))

def valid_subject(value):
    return isinstance(value,str) and re.fullmatch(r"[A-Za-z0-9_-]{16,128}",value) is not None

@dataclass(frozen=True)
class Principal:
    subject: str
    def __post_init__(self):
        if not valid_subject(self.subject):raise ValueError("Invalid identity subject")

class ProjectAccess:
    def __init__(self,store):self.store=store

    @staticmethod
    def metadata(project):
        access=project.get("access")
        if not isinstance(access,dict) or not valid_subject(access.get("owner_id")) or not isinstance(access.get("grants"),dict):return None
        return access

    def can(self,principal,project_id,permission):
        if not isinstance(principal,Principal):return False
        try:
            with self.store.lock:p=self.store._read(project_id)
        except EditorError:return False
        access=self.metadata(p)
        if not access:return False  # Unassigned legacy projects fail closed.
        owner=access["owner_id"]==principal.subject
        if permission=="own":return owner
        if permission not in PERMISSIONS or p.get("deleted_at"):return False
        if owner:return True
        grant=access["grants"].get(principal.subject)
        return isinstance(grant,list) and "view" in grant and permission in grant and all(x in PERMISSIONS for x in grant)

    def require(self,principal,project_id,permission):
        if not self.can(principal,project_id,permission):
            # Same response for absent, private, unassigned and revoked projects.
            raise EditorError("Projeto não encontrado ou sem permissão para esta ação.",404)

    def sharing(self,principal,project_id):
        with self.store.lock:
            self.require(principal,project_id,"own")
            p=self.store._read(project_id)
            return {"revision":p["revision"],**copy.deepcopy(p["access"])}

    def set_grant(self,principal,project_id,subject,permissions,expected_revision):
        with self.store.lock:
            self.require(principal,project_id,"own")
            p=self.store._read(project_id)
            if isinstance(expected_revision,bool) or expected_revision!=p["revision"]:
                raise EditorError("O projeto mudou. Atualize antes de alterar o compartilhamento.",409)
            if p.get("deleted_at"):raise EditorError("Restaure o projeto antes de compartilhar.",409)
            if not valid_subject(subject) or subject==p["access"]["owner_id"]:
                raise EditorError("Escolha outro usuário válido. O proprietário não pode ser alterado aqui.")
            if (not isinstance(permissions,list) or len(permissions)>len(PERMISSIONS)
                    or any(not isinstance(x,str) or x not in PERMISSIONS for x in permissions)
                    or len(set(permissions))!=len(permissions) or (permissions and "view" not in permissions)):
                raise EditorError("Permissões inválidas. Toda autorização precisa incluir visualização.")
            grants=p["access"]["grants"]
            if permissions:
                if subject not in grants and len(grants)>=100:raise EditorError("Limite de colaboradores atingido.",409)
                grants[subject]=sorted(permissions)
            else:grants.pop(subject,None)
            self.store._touch(p,"user:"+principal.subject,"sharing_update")
            self.store._write(p)
            return self.sharing(principal,project_id)
