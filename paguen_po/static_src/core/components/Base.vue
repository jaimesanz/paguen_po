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
                                <span>John Doe</span>
                                <span>Vivienda 1</span>
                            </div>
                        </md-list-item>
                    </md-list>
                </md-toolbar>

                <md-list>

                    <md-list-item>
                        <router-link to="/" @click.native="$refs.sidebar.toggle()">
                            <md-icon md-iconset="fa fa-lg fa-home"></md-icon>
                            <span>Home</span>
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

                        <span style="flex: 1"></span>

                        <md-button class="md-icon-button">
                            <md-icon md-iconset="fa fa-lg fa-user"></md-icon>
                        </md-button>
                    </div>
                    <div class="md-toolbar-container">
                        <h2 class="md-title">Home</h2>
                    </div>
                </md-toolbar>
            </md-whiteframe>
        </div>

    </div>
</template>

<script>
    export default {
        name: "paguenpo",
        data () {
            return {
                asdf: "holaaa"
            };
        }
    }
</script>