from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    if old not in text:
        raise SystemExit(f"Expected snippet not found in {path}: {old[:100]!r}")
    file.write_text(text.replace(old, new, 1))


replace_once(
    "web/src/client/routes.ts",
    "export const STORY_CHAPTERS_ROUTE = '/story/chapters';\nexport const MEMORY_CREATE_ROUTE = '/story/memories/new';",
    "export const STORY_CHAPTERS_ROUTE = '/story/chapters';\nexport const STORY_YEARS_ROUTE = '/story/years';\nexport const STORY_YEAR_ROUTE_PATTERN = '/story/years/:year';\nexport const MEMORY_CREATE_ROUTE = '/story/memories/new';",
)
replace_once(
    "web/src/client/routes.ts",
    "export function milestoneEditPath(milestoneId: string): string {\n  return `${milestoneDetailPath(milestoneId)}/edit`;\n}\n\nexport function wishDetailPath(wishId: string): string {",
    "export function milestoneEditPath(milestoneId: string): string {\n  return `${milestoneDetailPath(milestoneId)}/edit`;\n}\n\nexport function storyYearPath(year: number): string {\n  return `/story/years/${encodeURIComponent(String(year))}`;\n}\n\nexport function wishDetailPath(wishId: string): string {",
)

replace_once(
    "web/src/App.tsx",
    "  STORY_CHAPTERS_ROUTE,\n  WISH_DETAIL_ROUTE_PATTERN,\n} from './client/routes';",
    "  STORY_CHAPTERS_ROUTE,\n  STORY_YEAR_ROUTE_PATTERN,\n  STORY_YEARS_ROUTE,\n  WISH_DETAIL_ROUTE_PATTERN,\n} from './client/routes';",
)
replace_once(
    "web/src/App.tsx",
    "import { StoryProductPage } from './components/StoryProductPage';\nimport { ThemeControl } from './components/ThemeControl';",
    "import { StoryProductPage } from './components/StoryProductPage';\nimport {\n  StoryYearDetailPage,\n  StoryYearsIndexPage,\n} from './components/StoryYearsPage';\nimport { ThemeControl } from './components/ThemeControl';",
)
story_route = (
    "          <Route\n"
    "            path={appRoutePath('story')}\n"
    "            element={\n"
    "              <StoryProductPage\n"
    "                apis={apis}\n"
    "                accountId={account.id}\n"
    "                spaceId={spaceId}\n"
    "                loadMemoryImage={loadMemoryImage}\n"
    "                profilesApi={profilesApi}\n"
    "              />\n"
    "            }\n"
    "          />\n"
)
year_routes = story_route + (
    "          <Route\n"
    "            path={STORY_YEARS_ROUTE}\n"
    "            element={\n"
    "              <StoryYearsIndexPage\n"
    "                apis={apis}\n"
    "                accountId={account.id}\n"
    "                spaceId={spaceId}\n"
    "                loadMemoryImage={loadMemoryImage}\n"
    "                profilesApi={profilesApi}\n"
    "              />\n"
    "            }\n"
    "          />\n"
    "          <Route\n"
    "            path={STORY_YEAR_ROUTE_PATTERN}\n"
    "            element={\n"
    "              <StoryYearDetailPage\n"
    "                apis={apis}\n"
    "                accountId={account.id}\n"
    "                spaceId={spaceId}\n"
    "                loadMemoryImage={loadMemoryImage}\n"
    "                profilesApi={profilesApi}\n"
    "              />\n"
    "            }\n"
    "          />\n"
)
replace_once("web/src/App.tsx", story_route, year_routes)

replace_once(
    "web/src/components/StoryProductPage.tsx",
    "  milestoneDetailPath,\n  STORY_CHAPTERS_ROUTE,\n} from '../client/routes';",
    "  milestoneDetailPath,\n  STORY_CHAPTERS_ROUTE,\n  STORY_YEARS_ROUTE,\n  storyYearPath,\n} from '../client/routes';",
)
replace_once(
    "web/src/components/StoryProductPage.tsx",
    "  const uniqueYears = useMemo(() => {\n    const years = new Set<number>();\n    for (const item of items) {\n      years.add(item.effectiveDate.getFullYear());\n    }\n    return Array.from(years).sort((a, b) => b - a);\n  }, [items]);\n\n",
    "",
)
story_file = Path("web/src/components/StoryProductPage.tsx")
story_text = story_file.read_text()
start_marker = "          {/* 4. Year Archive */}"
end_marker = "        </div>\n      ) : combinedStory && (activeView === 'timeline' || hasActiveFilters) ? ("
start = story_text.find(start_marker)
end = story_text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate StoryProductPage year archive block")
replacement = """          {/* 4. Year Archive — availability comes from the authorized
              server projection, never from the currently loaded page. */}
          {availableYears.length > 0 ? (
            <section
              className="momente-year-archive"
              aria-labelledby="momente-years-heading"
            >
              <div className="momente-section-header">
                <div>
                  <h3
                    id="momente-years-heading"
                    className="momente-section-title"
                  >
                    {t('story.yearArchiveTitle')}
                  </h3>
                  <p className="momente-section-subhead">
                    {t('story.yearArchiveSubtitle')}
                  </p>
                </div>
                <Link
                  to={STORY_YEARS_ROUTE}
                  className="momente-stream-all-link"
                >
                  {t('story.yearArchiveAll')}
                </Link>
              </div>
              <div className="momente-year-pills">
                {availableYears.slice(0, 4).map((year) => (
                  <Link
                    key={year}
                    to={storyYearPath(year)}
                    className="momente-year-pill"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      width="14"
                      height="14"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                      className="year-pill-icon"
                    >
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                      <line x1="16" y1="2" x2="16" y2="6" />
                      <line x1="8" y1="2" x2="8" y2="6" />
                      <line x1="3" y1="10" x2="21" y2="10" />
                    </svg>
                    <span>{year}</span>
                  </Link>
                ))}
              </div>
            </section>
          ) : null}
"""
story_file.write_text(story_text[:start] + replacement + story_text[end:])

replace_once(
    "web/src/i18n/locales/de.ts",
    "    yearArchiveTitle: 'Jahre entdecken',\n    yearArchiveSubtitle:\n      'Direkt zu den Momenten eines bestimmten Jahres springen',\n",
    "    yearArchiveTitle: 'Unsere Jahre',\n    yearArchiveSubtitle: 'Eure gemeinsamen Momente, Jahr für Jahr.',\n    yearArchiveAll: 'Alle Jahre ansehen →',\n",
)
de_file = Path("web/src/i18n/locales/de.ts")
de_text = de_file.read_text()
marker = "  memory: {\n"
if marker not in de_text:
    raise SystemExit("Could not locate memory locale section")
years_locale = """  storyYears: {
    backToMoments: '← Zurück zu Momente',
    backToYears: '← Unsere Jahre',
    eyebrow: 'Jahresarchiv',
    title: 'Unsere Jahre',
    intro: 'Eure gemeinsame Geschichte, Jahr für Jahr.',
    listAria: 'Gemeinsame Jahre',
    currentYearLabel: 'Unser Jahr bisher',
    currentYearHint: 'Die Momente, die ihr dieses Jahr festgehalten habt.',
    pastYearLabel: 'Unser Jahr {{year}}',
    pastYearHint: 'Gemeinsame Momente aus diesem Jahr.',
    openYear: 'Unser Jahr {{year}} öffnen',
    detailTitle: 'Unser Jahr {{year}}',
    currentYearIntro:
      'Die Momente, die ihr {{year}} bisher miteinander festgehalten habt.',
    pastYearIntro:
      'Die gemeinsamen Momente, die ihr {{year}} festgehalten habt.',
    emptyTitle: 'Noch keine gemeinsamen Jahre',
    emptyBody:
      'Sobald ihr gemeinsame Momente festhaltet, findet ihr sie hier nach Jahren wieder.',
    unavailableTitle: 'Dieses Jahr ist noch leer',
    unavailableBody:
      'Für {{year}} gibt es keine gemeinsamen Momente in eurer Jahreschronik.',
    invalidTitle: 'Jahr nicht gefunden',
    invalidBody: 'Diese Jahresansicht ist nicht verfügbar.',
    loadMore: 'Weitere Momente laden',
    loadingMore: 'Weitere Momente werden geladen …',
    offline: 'Offline – zuletzt gespeicherte Jahreschronik',
  },
"""
de_file.write_text(de_text.replace(marker, years_locale + marker, 1))

css_file = Path("web/src/components/StoryYearsPage.css")
css_text = css_file.read_text()
if "text-decoration: none; /* #868-year-pill-link */" not in css_text:
    css_text += "\n.momente-year-pill {\n  text-decoration: none; /* #868-year-pill-link */\n}\n"
    css_file.write_text(css_text)
