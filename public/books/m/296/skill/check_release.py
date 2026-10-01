from typing import Any, Mapping


def check_release(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("release_id", "source_version", "skill_version"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            errors.append(f"缺少有效字段：{key}")

    if record.get("editorial_status") == "accepted":
        if not record.get("responsible_party"):
            errors.append("接受发布的记录缺少责任接口")

    if record.get("run_status") == "completed":
        if not record.get("output_refs"):
            errors.append("声称完成运行，但没有输出引用")

    if record.get("visibility") == "public":
        if not record.get("permission_checked"):
            errors.append("公开发布前尚未记录权限检查")

    if record.get("evidence_status") == "unexamined":
        if record.get("claim_label") == "validated_result":
            errors.append("证据状态与结果标签冲突")
    return errors
