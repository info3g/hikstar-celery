import Vue from "vue";
import "@/components/icons/hk-caret-down.js";
import "@/components/icons/hk-caret-up.js";

Vue.component("hk-sort-icon", {
  props: {
    header: {
      type: String,
      default: ""
    },
    sortBy: {
      type: Object,
      default: () => {
        return {
          key: "",
          ascending: true
        }
      }
    }
  },
  template: `
    <span>
      <template v-if="sortBy.key == header">
        <hk-caret-up v-if="sortBy.key === header && sortBy.ascending"></hk-caret-up>
        <hk-caret-down v-else></hk-caret-down>
      </template>
    </span>
  `
})
