from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"Expected exactly one match in {path}, found {count}: {old[:80]!r}"
        )
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


page = "web/src/components/ServerAdminPage.tsx"
replace_once(
    page,
    "                <th scope=\"col\">{t('serverAdmin.activity.change')}</th>\n                <th scope=\"col\">{t('serverAdmin.activity.changedAt')}</th>\n",
    "                <th scope=\"col\">{t('serverAdmin.activity.change')}</th>\n                <th scope=\"col\">{t('serverAdmin.activity.actor')}</th>\n                <th scope=\"col\">{t('serverAdmin.activity.changedAt')}</th>\n",
)
replace_once(
    page,
    "                  <td>\n                    {booleanStateLabel(item.previousValue, t)} →{' '}\n                    {booleanStateLabel(item.newValue, t)}\n                  </td>\n                  <td>{formatDate(item.createdAt) ?? '–'}</td>\n",
    "                  <td>\n                    {booleanStateLabel(item.previousValue, t)} →{' '}\n                    {booleanStateLabel(item.newValue, t)}\n                  </td>\n                  <td className=\"server-admin-actor-id\">\n                    {item.actorId ?? t('serverAdmin.activity.systemActor')}\n                  </td>\n                  <td>{formatDate(item.createdAt) ?? '–'}</td>\n",
)

locale = "web/src/i18n/locales/serverAdmin.ts"
replace_once(
    locale,
    "    change: 'Änderung',\n    changedAt: 'Geändert',\n",
    "    change: 'Änderung',\n    actor: 'Akteur',\n    systemActor: 'System / nicht mehr zugeordnet',\n    changedAt: 'Geändert',\n",
)

css = "web/src/components/ServerAdminPage.css"
replace_once(
    css,
    ".server-admin-table th {\n",
    ".server-admin-actor-id {\n  max-width: 16rem;\n  overflow-wrap: anywhere;\n  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;\n  font-size: 0.8125rem;\n}\n\n.server-admin-table th {\n",
)

test = "web/src/components/ServerAdminControls.test.tsx"
replace_once(
    test,
    "  it('renders privacy-safe audit changes without exposing actor ids', () => {\n",
    "  it('identifies the audit actor without exposing unrelated account data', () => {\n",
)
replace_once(
    test,
    "    expect(html.match(/<td>/g)).toHaveLength(3);\n    expect(html).not.toContain(actorId);\n",
    "    expect(html.match(/<td/g)).toHaveLength(4);\n    expect(html).toContain(actorId);\n",
)
