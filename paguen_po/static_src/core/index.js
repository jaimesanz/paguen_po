/*jslint browser: true */
/*global $, console, alert */
import Vue from 'vue';
import VueRouter from 'vue-router';
import Vuetify from 'vuetify';
import VueBreadcrumbs from 'vue-breadcrumbs';
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
Vue.use(VueBreadcrumbs, {
  template: '' +
  '<v-breadcrumbs divider="/" v-if="$breadcrumbs.length"> ' +
      '<v-breadcrumbs-item v-for="(crumb, key) in $breadcrumbs" :to="linkProp(crumb)" :key="key">' +
          '{{ crumb | crumbText }}' +
      '</v-breadcrumbs-item> ' +
  '</v-breadcrumbs>'
});

const routes = [
    {
        path: '/',
        component: Base,
        name: 'root',
        meta: {
            breadcrumb: 'Viviendas'
        },
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
                        meta: {
                            breadcrumb: 'Gastos'
                        },
                        props: true
                    }, {
                        path: 'budgets',
                        name: 'budgets',
                        component: Budgets,
                        meta: {
                            breadcrumb: 'Presupuestos'
                        }
                    }, {
                        path: 'shopping_lists',
                        name: 'shopping_lists',
                        component: ShoppingLists,
                        meta: {
                            breadcrumb: 'Listas'
                        }
                    }
                ]
            }
        ]
    }
];

const router = new VueRouter({
    // mode: 'history',
    routes: routes
});

new Vue({
    router
}).$mount('#app');
