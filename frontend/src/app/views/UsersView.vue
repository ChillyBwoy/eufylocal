<script setup lang="ts">
import { MudaButton, MudaErrorBox, MudaIcon, MudaSpinner } from "@mudakit/ui";
import { onMounted, ref } from "vue";

import { getUsers, type User } from "@/api";
import ApiResult from "@/app/components/ApiResult/ApiResult.vue";
import UserCreateDialog from "@/app/components/User/UserCreateDialog.vue";
import UserDeleteDialog from "@/app/components/User/UserDeleteDialog.vue";
import UserEditDialog from "@/app/components/User/UserEditDialog.vue";
import UserListItem from "@/app/components/User/UserListItem.vue";
import { useApi } from "@/app/composables/useApi";

const isCreateDialogOpen = ref(false);
const userToEdit = ref<User | null>(null);
const userToDelete = ref<User | null>(null);

const users = useApi(() => getUsers({ throwOnError: true }));

onMounted(() => {
  void users.dispatch();
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
      <section class="flex flex-col gap-4">
        <div class="flex items-center justify-between gap-4">
          <h2>Users</h2>
          <div class="flex items-center gap-3">
            <MudaButton type="button" variant="primary" @click="isCreateDialogOpen = true">
              <MudaIcon icon="add:outlined" />
              Add user
            </MudaButton>
          </div>
        </div>

        <div v-if="result.length > 0" class="grid grid-cols-3 gap-4">
          <UserListItem
            v-for="user in result"
            :key="user.id"
            :user="user"
            @update="userToEdit = user"
            @delete="userToDelete = user"
          />
        </div>
        <h3 v-else class="flex h-1/2 items-center justify-center text-center">No users yet</h3>
      </section>
    </template>
  </ApiResult>

  <UserCreateDialog v-model="isCreateDialogOpen" @created="users.dispatch" />
  <UserEditDialog v-model="userToEdit" @updated="users.dispatch" />
  <UserDeleteDialog v-model="userToDelete" @deleted="users.dispatch" />
</template>
