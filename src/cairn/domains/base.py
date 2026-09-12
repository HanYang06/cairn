"""领域基类、处理器注册表与领域异常。

数据基座固定（core 的 Manifest），领域通过 type + meta.props 扩展；
行为通过注册表按 type 分发。详见 `docs/architecture/domains.md`。
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, Self, runtime_checkable

from ..core.types import CairnError, ObjectInfo, Oid, SpaceId

if TYPE_CHECKING:
    from ..core.vault import Vault

UNSET: Any = object()


class DomainError(CairnError):
    """领域层错误基类。"""


class UnknownKindError(DomainError):
    """未注册的领域类型。"""


class KindMismatchError(DomainError):
    """对象类型与领域类不匹配。"""


@runtime_checkable
class Handler(Protocol):
    kind: str
    schema_version: int

    def normalize_meta(self, **fields: Any) -> dict[str, Any]: ...


_HANDLERS: dict[str, Handler] = {}


def register(handler: Handler) -> None:
    _HANDLERS[handler.kind] = handler


def get_handler(kind: str) -> Handler:
    try:
        return _HANDLERS[kind]
    except KeyError as exc:
        raise UnknownKindError(kind) from exc


def known_kinds() -> list[str]:
    return sorted(_HANDLERS)


class DomainObject:
    """领域对象基类：包裹 (Vault, OID, ObjectInfo) 的行为外壳。"""

    kind: ClassVar[str] = ""
    mime: ClassVar[str | None] = None
    schema_version: ClassVar[int] = 1

    def __init__(self, vault: Vault, oid: Oid, info: ObjectInfo) -> None:
        self._vault = vault
        self._oid = oid
        self._info = info

    @property
    def oid(self) -> Oid:
        return self._oid

    @property
    def info(self) -> ObjectInfo:
        return self._info

    @property
    def title(self) -> str | None:
        return self._info.title

    @property
    def tags(self) -> tuple[str, ...]:
        return self._info.tags

    @property
    def space_id(self) -> SpaceId:
        return self._info.space_id

    def meta(self) -> dict[str, Any]:
        return self._vault.meta(self._oid)

    def props(self) -> dict[str, Any]:
        return dict(self.meta().get("props") or {})

    def read(self) -> bytes:
        with self._vault.open(self._oid) as handle:
            return handle.read()

    def delete(self) -> None:
        self._vault.delete(self._oid)

    @classmethod
    def load(cls, vault: Vault, oid: Oid | str) -> Self:
        info = vault.info(oid)
        if info.type != cls.kind:
            raise KindMismatchError(f"期望 {cls.kind}，实际 {info.type}")
        return cls(vault, Oid.parse(str(oid)), info)

    @classmethod
    def list(
        cls,
        vault: Vault,
        *,
        space: str | SpaceId | None = None,
        tags: Iterable[str] | None = None,
    ) -> Iterator[Self]:
        for info in vault.iter(space=space, type=cls.kind, tags=tags):
            yield cls(vault, info.oid, info)

    def _put(self, payload: bytes, *, meta: dict[str, Any]) -> Oid:
        return self._vault.put(
            payload,
            oid=self._oid,
            space=self._info.space_id,
            type=self.kind,
            mime=self.mime,
            meta=meta,
        )

    def _refresh(self) -> None:
        self._info = self._vault.info(self._oid)
