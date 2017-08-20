<template>

    <v-app toolbar footer>
        <v-navigation-drawer
                temporary
                v-model="drawer"
                light
                overflow
                enable-resize-watcher
                absolute>

            <v-list two-lines>
                <v-list-tile avatar tag="div">
                    <v-list-tile-avatar>
                        <img src="https://api.adorable.io/avatars/face/eyes6/nose8/mouth6/2d7cc3" />
                    </v-list-tile-avatar>
                    <v-list-tile-content>
                        <v-list-tile-title>{{user.name}}</v-list-tile-title>
                        <v-list-tile-sub-title>
                            Vivienda 1
                        </v-list-tile-sub-title>
                    </v-list-tile-content>
                </v-list-tile>

            </v-list>
            
            <v-divider></v-divider>

            <v-list>
                <v-list-tile @click="drawer = false" :append="true" :to="{name: 'households'}">
                    <v-list-tile-action>
                        <v-icon medium>fa-home</v-icon>
                    </v-list-tile-action>
                    <v-list-tile-title>Viviendas</v-list-tile-title>
                </v-list-tile>
            </v-list>
        </v-navigation-drawer>
        <v-toolbar fixed class="teal" dark>
            <v-toolbar-side-icon @click.stop="drawer = !drawer"></v-toolbar-side-icon>
            <v-toolbar-title>
                <v-breadcrumbs divider="/" v-if="$route.matched.length">
                    <v-breadcrumbs-item v-for="(crumb, key) in $route.matched.filter(r => r.name !== 'root')" :to="{name: crumb.name, paramas: $route.params}" :key="key">
                        <span v-if="crumb.name === 'household'">
                            {{ $route.params.household_id }}
                        </span>
                        <span v-else>
                            {{ crumb.meta.breadcrumb}}
                        </span>
                    </v-breadcrumbs-item>
                </v-breadcrumbs>
            </v-toolbar-title>

            <v-spacer></v-spacer>

            <v-btn icon @click="signOut()">
                <v-icon>exit_to_app</v-icon>
            </v-btn>

        </v-toolbar>
        <main>
            <v-container fluid>
                <router-view></router-view>
            </v-container>
        </main>
        <v-footer>
            <v-spacer></v-spacer>
            <v-btn icon href="https://github.com/jaimesanz/paguen_po" target="_blank">
                <v-icon>fa-github</v-icon>
            </v-btn>
        </v-footer>
    </v-app>

</template>

<script>
    import axios from 'axios';
    import 'static_src/reverse';

    export default {
        name: "paguenpo",
        mounted: function () {
            "use strict";
            this.$nextTick(() => this.setUser());
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

<style>
    .breadcrumbs a {
        color: white;
    }

    ::selection {
        background: #e364ff; /* WebKit/Blink Browsers */
    }
    ::-moz-selection {
        background: #e364ff; /* Gecko Browsers */
    }
</style>