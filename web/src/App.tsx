import { useCallback, useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient, type UseQueryResult } from '@tanstack/react-query';
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import type { StoryPage as StoryPageData } from './api/generated/models/StoryPage';
import type { TokenView } from './api/generated/models/TokenView';
import { loadReferenceClientConfig } from './client/config';
import {
  createReferenceApis,
  loadAuthorizedImage,
  runMemoryMediaStoryFlow,
  signIn,
} from './client/referenceFlow';
import { StoryList } from './components/StoryList';
import { useTranslation } from './i18n';
