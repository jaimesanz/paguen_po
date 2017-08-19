<template>

    <v-app toolbar>
        <v-navigation-drawer
                temporary
                v-model="drawer"
                light
                overflow
                absolute>

            <v-list two-lines>
                <v-list-tile avatar tag="div">
                    <v-list-tile-avatar>
                        <img src="https://randomuser.me/api/portraits/men/85.jpg" />
                    </v-list-tile-avatar>
                    <v-list-tile-content>
                        <v-list-tile-title>{{user.name}}</v-list-tile-title>
                        <v-list-tile-sub-title>
                            Vivienda 1
                        </v-list-tile-sub-title>
                    </v-list-tile-content>
                </v-list-tile>
            </v-list>

            <v-list>
                <v-list-tile @click="drawer = false" :append="true" to="/">
                    <v-list-tile-action>
                        <v-icon>fa-home</v-icon>
                    </v-list-tile-action>
                    <v-list-tile-title>Viviendas</v-list-tile-title>
                </v-list-tile>
            </v-list>
        </v-navigation-drawer>
        <v-toolbar fixed class="deep-orange" dark>
            <v-toolbar-side-icon @click.stop="drawer = !drawer"></v-toolbar-side-icon>
            <v-toolbar-title>Viviendas</v-toolbar-title>

            <v-spacer></v-spacer>

            <v-btn icon @click="signOut()">
                <v-icon>fa-sign-out</v-icon>
            </v-btn>

        </v-toolbar>
        <main>
            <v-container fluid>
                <router-view></router-view>
            </v-container>
        </main>
    </v-app>

</template>

<script>
    import axios from 'axios';
    import 'static_src/reverse';

    export default {
        name: "paguenpo",
        mounted: function() {
            "use strict";
            this.$nextTick(function () {
                this.setUser();
            });
        },
        data () {
            return {
                drawer: false,
                user: {
                    name: "John Doex"
                }
            };
        },
        methods: {
            setUser () {
                axios.get(Urls["core:get_user_data"]())
                    .then(response => {
                        this.user = response.data['user'];
                    })
                    .catch(error => {
                        console.error(error);
                    });
            },
            signOut () {
                window.location = Urls["logout"]();
            }
        }
    }
</script>