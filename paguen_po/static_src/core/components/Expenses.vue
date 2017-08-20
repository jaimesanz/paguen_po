<template>
    <div>

        <p>Gastos Vivienda {{household_id}}</p>

        <v-data-table
                v-bind:headers="headers"
                :items="expenses"
                hide-actions
                class="elevation-1">
            <template slot="items" scope="props">
                <td class="text-xs-right">{{props.item.amount}}</td>
                <td class="text-xs-right">{{props.item.category}}</td>
                <td class="text-xs-right">{{props.item.user}}</td>
                <td class="text-xs-right">{{props.item.year}}</td>
                <td class="text-xs-right">{{props.item.month}}</td>
            </template>
        </v-data-table>

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
                headers: [
                    { text: 'Monto', value: 'amount' },
                    { text: 'Categoría', value: 'category' },
                    { text: 'Usuario', value: 'user' },
                    { text: 'Año', value: 'year' },
                    { text: 'Mes', value: 'month' },
                ],
                expenses: []
            };
        },
        methods: {
            setExpenses () {
                axios.get(Urls["api:expenses"](), {params: {
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