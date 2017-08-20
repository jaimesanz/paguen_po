<template>
    <div>
        <p>Vivienda {{household_id}}</p>
        <router-link :to="{ name: 'expenses' }">Gastos</router-link>
        <router-link :to="{ name: 'budgets' }">Presupuestos</router-link>
        <router-link :to="{ name: 'shopping_lists' }">Listas de Compras</router-link>
        <router-view></router-view>
    </div>
</template>

<script>
    import axios from 'axios';
    import 'static_src/reverse';

    export default {
        name: "household",
        props: ['household_id'],
        mounted: function () {
            this.$route.meta['breadcrumb'] = this.household_id;
        },
        data () {
            return {};
        }
    }
</script>