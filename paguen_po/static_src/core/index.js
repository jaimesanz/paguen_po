/*jslint browser: true */
/*global $, console, alert */
import Vue from 'vue';
import VueRouter from 'vue-router';
import Base from './components/Base.vue';

Vue.use(VueRouter);

const routes = [
    {
        path: '/',
        component: Base
    }
];

const router = new VueRouter({
    routes  // short for `routes: routes`
});

new Vue({
    'router': router
}).$mount('#app');
