<script setup lang="ts">
import { MudaButton, MudaErrorBox, MudaIcon } from "@mudakit/ui";
import { MudaCard } from "@mudakit/ui/MudaCard";
import { MudaSpinner } from "@mudakit/ui/MudaSpinner";
import { onMounted, ref } from "vue";

import { getUsers, type User } from "@/api";
import ApiResult from "@/app/components/ApiResult/ApiResult.vue";
import UserBadge from "@/app/components/User/UserBadge.vue";
import UserCreateDialog from "@/app/components/User/UserCreateDialog.vue";
import UserDeleteDialog from "@/app/components/User/UserDeleteDialog.vue";
import UserEditDialog from "@/app/components/User/UserEditDialog.vue";
import { useApi } from "@/app/composables/useApi";

const users = useApi(() => getUsers({ throwOnError: true }));
const isCreateDialogOpen = ref(false);
const userToEdit = ref<User | null>(null);
const userToDelete = ref<User | null>(null);

onMounted(async () => {
  await users.dispatch();
});
</script>

<template>
  <ApiResult :state="users.state.value">
    <template #idle>
      <div class="grid min-h-[50vh] place-items-center">
        <MudaSpinner size="large" label="Loading users" />
      </div>
    </template>

    <template #loading>
      <div class="grid min-h-[50vh] place-items-center">
        <MudaSpinner size="large" label="Loading users" />
      </div>
    </template>

    <template #failure="{ error }">
      <MudaErrorBox title="Unable to load users" :error="error" />
    </template>

    <template #body="{ result }">
      <section class="flex flex-col gap-5">
        <div class="flex items-end justify-between gap-4">
          <div>
            <p class="text-muda-primary font-mono text-xs tracking-[0.22em] uppercase">Profiles</p>
            <h2 class="mt-1 text-2xl font-semibold">Users</h2>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-muda-secondary font-mono text-sm">{{ result.length }}</span>
            <MudaButton type="button" variant="primary" @click="isCreateDialogOpen = true">
              <MudaIcon icon="add:outlined" />
              Add user
            </MudaButton>
          </div>
        </div>

        <div v-if="result.length" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <MudaCard v-for="user in result" :key="user.id" class="min-w-0">
            <div class="flex h-full min-h-32 flex-col justify-between gap-6">
              <div>
                <UserBadge :user="user" />
                <p class="text-muda-secondary mt-3 font-mono text-xs">User #{{ user.id }}</p>
              </div>

              <div class="flex justify-end gap-2">
                <MudaButton size="small" type="button" @click="userToEdit = user">
                  <MudaIcon icon="edit:outlined" />
                  Edit
                </MudaButton>
                <MudaButton size="small" type="button" variant="danger" @click="userToDelete = user">
                  <MudaIcon icon="delete:outlined" />
                  Delete
                </MudaButton>
              </div>
            </div>
          </MudaCard>
        </div>

        <MudaCard v-else class="border-muda-secondary-light grid min-h-48 place-items-center border-t text-center">
          <div>
            <p class="font-medium">No users yet</p>
            <p class="text-muda-secondary mt-2 text-sm">Add your first user to start assigning measurements.</p>
          </div>
        </MudaCard>
      </section>
    </template>
  </ApiResult>

  <UserCreateDialog v-model="isCreateDialogOpen" @created="users.dispatch" />
  <UserEditDialog v-model="userToEdit" @updated="users.dispatch" />
  <UserDeleteDialog v-model="userToDelete" @deleted="users.dispatch" />
</template>
