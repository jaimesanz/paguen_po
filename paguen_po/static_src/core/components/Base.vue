<template>
    <div>

        <div class="app-viewport">
            <md-sidenav class="md-left md-fixed" ref="sidebar">
                <md-toolbar class="md-account-header">
                    <md-list class="md-transparent">
                        <md-list-item class="md-avatar-list">
                            <img src="" alt="PaguenPo">
                        </md-list-item>

                        <md-list-item>
                            <div class="md-list-text-container">
                                <span>{{user.name}}</span>
                                <span>Vivienda 1</span>
                            </div>
                        </md-list-item>
                    </md-list>
                </md-toolbar>

                <md-list>

                    <md-list-item>
                        <router-link to="/" @click.native="$refs.sidebar.toggle()">
                            <md-icon md-iconset="fa fa-lg fa-home"></md-icon>
                            <span>Viviendas</span>
                        </router-link>
                    </md-list-item>

                </md-list>

            </md-sidenav>

            <md-whiteframe md-elevation="3" class="main-toolbar">
                <md-toolbar class="md-dense">
                    <div class="md-toolbar-container">
                        <md-button class="md-icon-button" @click="$refs.sidebar.toggle()">
                            <md-icon md-iconset="fa fa-lg fa-bars"></md-icon>
                        </md-button>

                        <h2 class="md-title">Viviendas</h2>

                        <span style="flex: 1"></span>

                        <md-button class="md-icon-button">
                            <md-icon md-iconset="fa fa-lg fa-sign-out" @click.native="signOut()"></md-icon>
                        </md-button>
                    </div>
                </md-toolbar>
            </md-whiteframe>
        </div>

        <router-view></router-view>

    </div>
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