<template>
    <div>
        <div v-if="households.length > 0">
            <p v-for="house in households">
                <router-link :to="{name: 'household', params: {household_id: house.id}}">
                    {{house.name}}
                </router-link>
            </p>
        </div>
        <div v-else>
            No hay viviendas para este usuario!
        </div>
    </div>
</template>

<script>
    import axios from 'axios';
    import 'static_src/reverse';

    export default {
        name: "households",
        mounted: function() {
            "use strict";
            this.$nextTick(function () {
                this.setHouseholds();
            });
        },
        data () {
            return {
                households: []
            };
        },
        methods: {
            setHouseholds () {
                axios.get(Urls["households:list"]())
                    .then(response => {
                        this.households= response.data;
                    })
                    .catch(error => {
                        console.error(error);
                    });
            }
        }
    }
</script>