/*jslint browser: true */
/*global $, console, alert */
import Vue from 'vue';
import VueRouter from 'vue-router';
import Vuetify from 'vuetify';
import 'vuetify/dist/vuetify.min.css';
import Base from './components/Base.vue';
import Households from './components/Households.vue';
import Household from './components/Household.vue';
import Expenses from './components/Expenses.vue';
import Budgets from './components/Budgets.vue';
import ShoppingLists from './components/ShoppingLists.vue';
import 'font-awesome-sass-loader';

Vue.use(VueRouter);
Vue.use(Vuetify);

const routes = [
    {
        path: '/',
        component: Base,
        children: [
            {
                path: '',
                name: 'households',
                component: Households
            }, {
                path: 'vivienda/:household_id',
                name: "household",
                component: Household,
                props: true,
                children: [
                    {
                        path: 'expenses',
                        name: 'expenses',
                        component: Expenses,
                        props: true
                    }, {
                        path: 'budgets',
                        name: 'budgets',
                        component: Budgets
                    }, {
                        path: 'shopping_lists',
                        name: 'shopping_lists',
                        component: ShoppingLists
                    }
                ]
            }
        ]
    }
];

const router = new VueRouter({
    routes  // short for `routes: routes`
});

new Vue({
    router: router
}).$mount('#app');
