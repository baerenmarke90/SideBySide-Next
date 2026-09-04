import { Link } from 'react-router-dom';
import { PRIVATE_AREA_ROOT_PATH } from '../client/privateArea';
import {
  MORE_PEOPLE_ROUTE,
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
 * Secondary destinations that do not have persistent header actions.
 * Notifications, Profile, and Settings are accessed directly from the header.
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

      <ul className="more-destinations layout-columns">
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
