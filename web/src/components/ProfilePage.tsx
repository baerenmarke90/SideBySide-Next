import type { AccountView } from '../api/generated/models/AccountView';
import { PartnerConnectionPanel } from './PartnerConnectionPanel';
import { ProfilePage as ProfilePageBase } from './ProfilePageBase';

export interface ProfilePageProps {
  apiBaseUrl: string;
  accessToken: string;
  account: AccountView;
  spaceId: string;
}

export function ProfilePage(props: ProfilePageProps) {
  return (
    <>
      <ProfilePageBase {...props} />
      <PartnerConnectionPanel {...props} />
    </>
  );
}
