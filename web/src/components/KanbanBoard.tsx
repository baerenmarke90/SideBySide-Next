import { useState, useCallback, type FormEvent, type ReactNode } from 'react';
import {
  DragDropContext,
  Droppable,
  Draggable,
  type DropResult,
} from '@hello-pangea/dnd';
import { Link } from 'react-router-dom';
import { useTranslation } from '../i18n';
import type { WishDetail } from '../api/generated/models/WishDetail';
import type { PlanDetail } from '../api/generated/models/PlanDetail';
import type { SharedPlanningApis } from '../client/sharedPlanning';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { wishDetailPath, planDetailPath } from '../client/routes';
import { ProblemState } from './ProblemState';

interface KanbanBoardProps {
  apis: SharedPlanningApis;
  spaceId: string;
  wishes: WishDetail[];
  plans: PlanDetail[];
  placeChoices?: ReactNode;
  onCreateWish: (title: string, onSuccess: () => void) => void;
  onCreatePlan: (
    values: { title: string; description?: string; placeId?: string },
    onSuccess: () => void,
  ) => void;
  createWishPending?: boolean;
  createPlanPending?: boolean;
  createWishError?: Error | null;
  createPlanError?: Error | null;
}

export function KanbanBoard({
  apis,
  spaceId,
  wishes,
  plans,
  placeChoices,
  onCreateWish,
  onCreatePlan,
  createWishPending = false,
  createPlanPending = false,
  createWishError = null,
  createPlanError = null,
}: KanbanBoardProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const [showWishForm, setShowWishForm] = useState(false);
  const [showPlanForm, setShowPlanForm] = useState(false);

  const openWishes = wishes.filter((w) => w.status === 'OPEN');
  const plannedPlans = plans.filter((p) => p.status !== 'COMPLETED');
  const completedPlans = plans.filter((p) => p.status === 'COMPLETED');

  // Mutations
  const convertToPlan = useMutation({
    mutationFn: (wish: WishDetail) =>
      apis.plans.convertWishToPlan({
        spaceId,
        wishId: wish.id,
        ifMatch: String(wish.version),
        wishToPlan: {},
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'wishes', spaceId],
      });
      queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'plans', spaceId],
      });
    },
  });

  const completePlan = useMutation({
    mutationFn: (plan: PlanDetail) =>
      apis.plans.completePlan({
        spaceId,
        planId: plan.id,
        ifMatch: String(plan.version),
        planComplete: { experiencedOn: new Date() },
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: ['m5-s3', 'plans', spaceId],
      }),
  });

  const onDragEnd = useCallback(
    (result: DropResult) => {
      const { source, destination } = result;
      if (!destination) return;

      if (
        source.droppableId === 'wishes' &&
        destination.droppableId === 'plans'
      ) {
        const wish = openWishes[source.index];
        if (wish) convertToPlan.mutate(wish);
      } else if (
        source.droppableId === 'plans' &&
        destination.droppableId === 'completed'
      ) {
        const plan = plannedPlans[source.index];
        if (plan) completePlan.mutate(plan);
      }
    },
    [openWishes, plannedPlans, convertToPlan, completePlan],
  );

  function handleWishSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);
    const title = String(data.get('title')).trim();
    if (!title) return;
    onCreateWish(title, () => {
      form.reset();
      setShowWishForm(false);
    });
  }

  function handlePlanSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);
    const title = String(data.get('title')).trim();
    if (!title) return;
    const description = String(data.get('description')).trim();
    const placeId = String(data.get('placeId')).trim();
    onCreatePlan(
      {
        title,
        description: description || undefined,
        placeId: placeId || undefined,
      },
      () => {
        form.reset();
        setShowPlanForm(false);
      },
    );
  }

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="kanban-container">
        <div className="kanban-grid">
          {/* Column 1: Wishes */}
          <Droppable droppableId="wishes">
            {(provided, snapshot) => (
              <div
                className={`kanban-column ${snapshot.isDraggingOver ? 'kanban-column-dragover' : ''}`}
                ref={provided.innerRef}
                {...provided.droppableProps}
              >
                <div className="kanban-column-header">
                  <div className="kanban-header-title-group">
                    <span className="kanban-dot dot-wish" aria-hidden="true" />
                    <h3>{t('m5s3.wish.heading')}</h3>
                    <span className="kanban-count-pill">
                      {openWishes.length}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="kanban-add-trigger"
                    onClick={() => setShowWishForm(!showWishForm)}
                    aria-label={t('m5s3.wish.create')}
                  >
                    {showWishForm ? '✕' : '+'}
                  </button>
                </div>

                {showWishForm && (
                  <form
                    onSubmit={handleWishSubmit}
                    className="kanban-inline-form"
                  >
                    <input
                      name="title"
                      required
                      maxLength={200}
                      placeholder={t('m5s3.common.title')}
                    />
                    <div className="kanban-form-actions">
                      <button
                        type="button"
                        className="tertiary"
                        onClick={() => setShowWishForm(false)}
                      >
                        {t('common.cancel')}
                      </button>
                      <button type="submit" disabled={createWishPending}>
                        {createWishPending
                          ? t('m5s3.common.saving')
                          : t('m5s3.common.save')}
                      </button>
                    </div>
                    {createWishError ? (
                      <ProblemState error={createWishError} />
                    ) : null}
                  </form>
                )}

                <div className="kanban-cards-list">
                  {openWishes.map((wish, index) => (
                    <Draggable
                      key={wish.id}
                      draggableId={wish.id}
                      index={index}
                    >
                      {(provided, snapshot) => (
                        <div
                          className={`kanban-card ${snapshot.isDragging ? 'kanban-card-dragging' : ''}`}
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          style={provided.draggableProps.style}
                        >
                          <div className="kanban-card-content">
                            <h4>{wish.title}</h4>
                            <div className="kanban-card-footer">
                              <span className="kanban-badge badge-wish">
                                Idee
                              </span>
                              <Link
                                to={wishDetailPath(wish.id)}
                                className="kanban-card-link"
                                onClick={(e) => e.stopPropagation()}
                              >
                                {t('m5s3.common.open')} →
                              </Link>
                            </div>
                          </div>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                  {openWishes.length === 0 && !showWishForm && (
                    <div className="kanban-empty-placeholder">
                      {t('m5s3.wish.intro')}
                    </div>
                  )}
                </div>
              </div>
            )}
          </Droppable>

          {/* Column 2: Plans */}
          <Droppable droppableId="plans">
            {(provided, snapshot) => (
              <div
                className={`kanban-column ${snapshot.isDraggingOver ? 'kanban-column-dragover' : ''}`}
                ref={provided.innerRef}
                {...provided.droppableProps}
              >
                <div className="kanban-column-header">
                  <div className="kanban-header-title-group">
                    <span className="kanban-dot dot-plan" aria-hidden="true" />
                    <h3>{t('m5s3.plan.heading')}</h3>
                    <span className="kanban-count-pill">
                      {plannedPlans.length}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="kanban-add-trigger"
                    onClick={() => setShowPlanForm(!showPlanForm)}
                    aria-label={t('m5s3.plan.create')}
                  >
                    {showPlanForm ? '✕' : '+'}
                  </button>
                </div>

                {showPlanForm && (
                  <form
                    onSubmit={handlePlanSubmit}
                    className="kanban-inline-form"
                  >
                    <input
                      name="title"
                      required
                      maxLength={200}
                      placeholder={t('m5s3.common.title')}
                    />
                    <textarea
                      name="description"
                      rows={2}
                      placeholder={t('m5s3.common.description')}
                    />
                    {placeChoices && (
                      <select name="placeId" defaultValue="">
                        <option value="">{t('m5s3.common.noPlace')}</option>
                        {placeChoices}
                      </select>
                    )}
                    <div className="kanban-form-actions">
                      <button
                        type="button"
                        className="tertiary"
                        onClick={() => setShowPlanForm(false)}
                      >
                        {t('common.cancel')}
                      </button>
                      <button type="submit" disabled={createPlanPending}>
                        {createPlanPending
                          ? t('m5s3.common.saving')
                          : t('m5s3.common.save')}
                      </button>
                    </div>
                    {createPlanError ? (
                      <ProblemState error={createPlanError} />
                    ) : null}
                  </form>
                )}

                <div className="kanban-cards-list">
                  {plannedPlans.map((plan, index) => (
                    <Draggable
                      key={plan.id}
                      draggableId={plan.id}
                      index={index}
                    >
                      {(provided, snapshot) => (
                        <div
                          className={`kanban-card ${snapshot.isDragging ? 'kanban-card-dragging' : ''}`}
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          style={provided.draggableProps.style}
                        >
                          <div className="kanban-card-content">
                            <h4>{plan.title}</h4>
                            {plan.description && (
                              <p className="kanban-card-excerpt">
                                {plan.description}
                              </p>
                            )}
                            <div className="kanban-card-footer">
                              {plan.placeId ? (
                                <span className="kanban-badge badge-place">
                                  📍 Ort verknüpft
                                </span>
                              ) : (
                                <span className="kanban-badge badge-plan">
                                  In Planung
                                </span>
                              )}
                              <Link
                                to={planDetailPath(plan.id)}
                                className="kanban-card-link"
                                onClick={(e) => e.stopPropagation()}
                              >
                                {t('m5s3.common.open')} →
                              </Link>
                            </div>
                          </div>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                  {plannedPlans.length === 0 && !showPlanForm && (
                    <div className="kanban-empty-placeholder">
                      Wünsche hierher ziehen, um sie zu planen
                    </div>
                  )}
                </div>
              </div>
            )}
          </Droppable>

          {/* Column 3: Completed */}
          <Droppable droppableId="completed">
            {(provided, snapshot) => (
              <div
                className={`kanban-column ${snapshot.isDraggingOver ? 'kanban-column-dragover' : ''}`}
                ref={provided.innerRef}
                {...provided.droppableProps}
              >
                <div className="kanban-column-header">
                  <div className="kanban-header-title-group">
                    <span
                      className="kanban-dot dot-completed"
                      aria-hidden="true"
                    />
                    <h3>Erledigt</h3>
                    <span className="kanban-count-pill">
                      {completedPlans.length}
                    </span>
                  </div>
                </div>

                <div className="kanban-cards-list">
                  {completedPlans.map((plan, index) => (
                    <Draggable
                      key={plan.id}
                      draggableId={plan.id}
                      index={index}
                      isDragDisabled
                    >
                      {(provided) => (
                        <div
                          className="kanban-card kanban-card-completed"
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          style={provided.draggableProps.style}
                        >
                          <div className="kanban-card-content">
                            <h4>{plan.title}</h4>
                            <div className="kanban-card-footer">
                              <span className="kanban-badge badge-completed">
                                ✅ Erledigt
                              </span>
                              <Link
                                to={planDetailPath(plan.id)}
                                className="kanban-card-link"
                              >
                                {t('m5s3.common.open')} →
                              </Link>
                            </div>
                          </div>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                  {completedPlans.length === 0 && (
                    <div className="kanban-empty-placeholder">
                      Pläne hierher ziehen, wenn sie erledigt sind
                    </div>
                  )}
                </div>
              </div>
            )}
          </Droppable>
        </div>
      </div>
    </DragDropContext>
  );
}
