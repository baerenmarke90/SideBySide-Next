import { Link } from 'react-router-dom';
import { PRIVATE_AREA_ROOT_PATH } from '../client/privateArea';
import {
  MORE_NOTIFICATIONS_ROUTE,
  MORE_PEOPLE_ROUTE,
  MORE_PROFILE_ROUTE,
  MORE_SETTINGS_ROUTE,
  type AppRouteIcon,
} from '../client/routes';
import { useTranslation } from '../i18n';
import { DestinationIcon } from './DestinationIcon';
import { PageHeader } from './PageHeader';
import './MoreOverviewPage.css';

interface MoreDestination {
  path: string;
  icon: AppRouteIcon;
  titleKey: string;
  descriptionKey: string;
}

/**
 * Everything that is not a primary task lives here, per
 * `docs/INFORMATION-ARCHITECTURE.md` section 5. Each entry says what it is for,
 * because an area overview that only lists names makes the user open pages to
 * find out what they contain.
 */
const MORE_DESTINATIONS: readonly MoreDestination[] = [
  {
    path: MORE_PEOPLE_ROUTE,
    icon: 'people',
    titleKey: 'more.people.title',
    descriptionKey: 'more.people.description',
  },
  {
    path: PRIVATE_AREA_ROOT_PATH,
    icon: 'private',
    titleKey: 'more.private.title',
    descriptionKey: 'more.private.description',
  },
  {
    path: MORE_NOTIFICATIONS_ROUTE,
    icon: 'notifications',
    titleKey: 'more.notifications.title',
    descriptionKey: 'more.notifications.description',
  },
  {
    path: MORE_PROFILE_ROUTE,
    icon: 'profile',
    titleKey: 'more.profile.title',
    descriptionKey: 'more.profile.description',
  },
  {
    path: MORE_SETTINGS_ROUTE,
    icon: 'settings',
    titleKey: 'more.settings.title',
    descriptionKey: 'more.settings.description',
  },
];

export function MoreOverviewPage() {
  const { t } = useTranslation();

  return (
    <div className="page">
      <PageHeader
        eyebrow={t('more.eyebrow')}
        title={t('more.title')}
        description={t('more.intro')}
      />

      <ul className="more-destinations layout-columns layout-columns-dense">
        {MORE_DESTINATIONS.map((destination) => (
          <li key={destination.path}>
            <Link className="more-destination" to={destination.path}>
              <span className="more-destination-icon" aria-hidden="true">
                <DestinationIcon icon={destination.icon} />
              </span>
              <span className="more-destination-copy">
                <strong>{t(destination.titleKey)}</strong>
                <span>{t(destination.descriptionKey)}</span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
