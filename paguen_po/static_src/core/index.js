/*jslint browser: true */
/*global $, console, alert */
import Vue from 'vue';
import VueRouter from 'vue-router';
import VueMaterial from 'vue-material';
import 'vue-material/dist/vue-material.css';
import Base from './components/Base.vue';
import 'font-awesome-sass-loader';

Vue.use(VueRouter);
Vue.use(VueMaterial);

const routes = [
    {
        path: '/',
        component: Base
    }
];

Vue.material.registerTheme({
    default: {
        primary: 'teal',
        accent: 'pink'
    }
});

const router = new VueRouter({
    routes  // short for `routes: routes`
});

new Vue({
    'router': router
}).$mount('#app');
