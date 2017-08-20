<template>
    <div v-if="$route.name === 'household'">
        <h5>Vivienda {{household_id}}</h5>
        <router-link :to="{ name: 'expenses' }">Gastos</router-link>
        <router-link :to="{ name: 'budgets' }">Presupuestos</router-link>
        <router-link :to="{ name: 'shopping_lists' }">Listas de Compras</router-link>
    </div>
    <div v-else>
        <router-view></router-view>
    </div>
</template>

<script>
    import axios from 'axios';
    import 'static_src/reverse';

    export default {
        name: "household",
        props: ['household_id'],
        data () {
            return {};
        }
    }
</script>