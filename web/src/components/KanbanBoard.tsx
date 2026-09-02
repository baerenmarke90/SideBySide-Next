import { useCallback } from 'react';
import {
  DragDropContext,
  Droppable,
  Draggable,
  type DropResult,
} from '@hello-pangea/dnd';
import { useTranslation } from '../i18n';
import type { WishDetail } from '../api/generated/models/WishDetail';
import type { PlanDetail } from '../api/generated/models/PlanDetail';
import type { SharedPlanningApis } from '../client/sharedPlanning';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface KanbanBoardProps {
  apis: SharedPlanningApis;
  spaceId: string;
  wishes: WishDetail[];
  plans: PlanDetail[];
}

export function KanbanBoard({
  apis,
  spaceId,
  wishes,
  plans,
}: KanbanBoardProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

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
      queryClient.invalidateQueries({ queryKey: ['m5-s3', 'wishes', spaceId] });
      queryClient.invalidateQueries({ queryKey: ['m5-s3', 'plans', spaceId] });
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
      queryClient.invalidateQueries({ queryKey: ['m5-s3', 'plans', spaceId] }),
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

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div
        className="kanban-board layout-columns"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1rem',
        }}
      >
        {/* Column 1: Wishes */}
        <Droppable droppableId="wishes">
          {(provided) => (
            <div
              className="kanban-column layout-panel"
              ref={provided.innerRef}
              {...provided.droppableProps}
            >
              <h3 className="kanban-column-title">
                {t('m5s3.wish.heading')} (Ideen)
              </h3>
              {openWishes.map((wish, index) => (
                <Draggable key={wish.id} draggableId={wish.id} index={index}>
                  {(provided) => (
                    <div
                      className="kanban-card m4-item"
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      {...provided.dragHandleProps}
                      style={{
                        marginBottom: '8px',
                        ...provided.draggableProps.style,
                      }}
                    >
                      <h4>{wish.title}</h4>
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>

        {/* Column 2: Plans */}
        <Droppable droppableId="plans">
          {(provided) => (
            <div
              className="kanban-column layout-panel"
              ref={provided.innerRef}
              {...provided.droppableProps}
            >
              <h3 className="kanban-column-title">
                {t('m5s3.plan.heading')} (In Planung)
              </h3>
              {plannedPlans.map((plan, index) => (
                <Draggable key={plan.id} draggableId={plan.id} index={index}>
                  {(provided) => (
                    <div
                      className="kanban-card m4-item"
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      {...provided.dragHandleProps}
                      style={{
                        marginBottom: '8px',
                        ...provided.draggableProps.style,
                      }}
                    >
                      <h4>{plan.title}</h4>
                      {plan.placeId ? (
                        <span className="m4-item-kind">📍 Ort verknüpft</span>
                      ) : null}
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>

        {/* Column 3: Completed */}
        <Droppable droppableId="completed">
          {(provided) => (
            <div
              className="kanban-column layout-panel"
              ref={provided.innerRef}
              {...provided.droppableProps}
            >
              <h3 className="kanban-column-title">Erledigt</h3>
              {completedPlans.map((plan, index) => (
                <Draggable
                  key={plan.id}
                  draggableId={plan.id}
                  index={index}
                  isDragDisabled
                >
                  {(provided) => (
                    <div
                      className="kanban-card m4-item"
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      {...provided.dragHandleProps}
                      style={{
                        marginBottom: '8px',
                        opacity: 0.7,
                        ...provided.draggableProps.style,
                      }}
                    >
                      <h4>{plan.title}</h4>
                      <span className="m4-item-kind">✅ Erledigt</span>
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </div>
    </DragDropContext>
  );
}
