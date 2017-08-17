<template>
    <div>

        <p>Asdf {{household_id}}</p>

        <md-table>
            <md-table-header>
                <md-table-row>
                    <md-table-head>Monto</md-table-head>
                    <md-table-head>Categoría</md-table-head>
                    <md-table-head>Usuario</md-table-head>
                    <md-table-head>Año</md-table-head>
                    <md-table-head>Mes</md-table-head>
                </md-table-row>
            </md-table-header>

            <md-table-body>
                <md-table-row v-for="(expense, index) in expenses" :key="index">
                    <md-table-cell>{{expense.amount}}</md-table-cell>
                    <md-table-cell>{{expense.category}}</md-table-cell>
                    <md-table-cell>{{expense.user}}</md-table-cell>
                    <md-table-cell>{{expense.year}}</md-table-cell>
                    <md-table-cell>{{expense.month}}</md-table-cell>
                </md-table-row>
            </md-table-body>
        </md-table>
    </div>
</template>

<script>
    import axios from 'axios';
    import 'static_src/reverse';

    export default {
        name: "expenses",
        props: ['household_id'],
        mounted: function() {
            "use strict";
            this.$nextTick(function () {
                this.setExpenses();
            });
        },
        data () {
            return {
                expenses: []
            };
        },
        methods: {
            setExpenses () {
                axios.get(Urls["expenses:list"](), {params: {
                    'household': this.household_id
                }}).then(response => {
                    this.expenses = response.data;
                }).catch(error => {
                    console.error(error);
                });
            }
        }
    }
</script>