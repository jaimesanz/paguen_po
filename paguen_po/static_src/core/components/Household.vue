<template>
    <div>
        <div v-if="expenses.length > 0">
            <p v-for="expense in expenses">
                hoalaa
            </p>
        </div>
        <div v-else>
            :(
        </div>
    </div>
</template>

<script>
    import axios from 'axios';
    import 'static_src/reverse';

    export default {
        name: "household",
        props: ['id'],
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
                    'household': this.id
                }}).then(response => {
                    this.expenses = response.data;
                }).catch(error => {
                    console.error(error);
                });
            }
        }
    }
</script>