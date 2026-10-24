/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { today, serializeDate } from "@web/core/l10n/dates";
import { Component, onWillStart, useState, useRef, useEffect } from "@odoo/owl";

// Same accent palette as the Sales dashboard (dandot_sale_order_dashboard),
// plus "gray" for the neutral "New" state which that dashboard has no
// equivalent of.
const COLOR_HEX = {
    blue: "#4c6ef5",
    purple: "#7c3aed",
    green: "#0ca678",
    amber: "#f59f00",
    red: "#e03131",
    gray: "#64748b",
};

const ISSUE_STATES = [
    { key: "new", label: "New", icon: "fa-file-o", color: "gray" },
    { key: "waiting_department_approval", label: "Waiting Department Approval", icon: "fa-hourglass-half", color: "amber" },
    { key: "waiting_head_approval", label: "Waiting Head Approval", icon: "fa-hourglass-end", color: "purple" },
    { key: "approved", label: "Approved", icon: "fa-thumbs-o-up", color: "green" },
    { key: "purchase_order_created", label: "Orders Created", icon: "fa-shopping-cart", color: "blue" },
    { key: "received", label: "Received", icon: "fa-check-square-o", color: "green" },
    { key: "cancelled", label: "Cancelled", icon: "fa-times-circle-o", color: "red" },
];

const RETURN_STATES = [
    { key: "new", label: "New", icon: "fa-file-o", color: "gray" },
    { key: "waiting_department_approval", label: "Waiting Department Approval", icon: "fa-hourglass-half", color: "amber" },
    { key: "waiting_head_approval", label: "Waiting Head Approval", icon: "fa-hourglass-end", color: "purple" },
    { key: "approved", label: "Approved", icon: "fa-thumbs-o-up", color: "green" },
    { key: "transfer_created", label: "Transfer Created", icon: "fa-exchange", color: "blue" },
    { key: "received", label: "Received", icon: "fa-check-square-o", color: "green" },
    { key: "cancelled", label: "Cancelled", icon: "fa-times-circle-o", color: "red" },
];

const DATE_PRESETS = [
    { id: "today", label: "Today" },
    { id: "yesterday", label: "Yesterday" },
    { id: "last_7_days", label: "Last 7 Days" },
    { id: "last_30_days", label: "Last 30 Days" },
    { id: "last_60_days", label: "Last 60 Days" },
    { id: "last_90_days", label: "Last 90 Days" },
];

function presetRange(presetId) {
    const t = today();
    switch (presetId) {
        case "today":
            return [t, t];
        case "yesterday":
            return [t.minus({ days: 1 }), t.minus({ days: 1 })];
        case "last_7_days":
            return [t.minus({ days: 6 }), t];
        case "last_60_days":
            return [t.minus({ days: 59 }), t];
        case "last_90_days":
            return [t.minus({ days: 89 }), t];
        case "last_30_days":
        default:
            return [t.minus({ days: 29 }), t];
    }
}

// Odoo's bundled Chart.js has no datalabels plugin, so bar values are drawn
// by hand - inside the bar (white) when it's tall enough to fit the text,
// otherwise just above it (in the theme's text color) so short/zero bars
// still get a legible label instead of overlapping the axis. Copied from
// the Sales dashboard (dandot_sale_order_dashboard) so both look identical.
const barValueLabels = {
    id: "barValueLabels",
    afterDatasetsDraw(chart) {
        const { decimals = 0, color = "#495057" } = chart.options.plugins.barValueLabels || {};
        const format = (value) =>
            new Intl.NumberFormat(undefined, {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals,
            }).format(value || 0);
        const { ctx } = chart;
        const dataset = chart.data.datasets[0];
        const meta = chart.getDatasetMeta(0);
        ctx.save();
        ctx.font = "bold 12px -apple-system, BlinkMacSystemFont, sans-serif";
        ctx.textAlign = "center";
        meta.data.forEach((bar, index) => {
            const label = format(dataset.data[index]);
            const barTop = Math.min(bar.y, bar.base);
            const barBottom = Math.max(bar.y, bar.base);
            const barHeight = barBottom - barTop;
            if (barHeight > 26) {
                ctx.fillStyle = "#ffffff";
                ctx.textBaseline = "top";
                ctx.fillText(label, bar.x, barTop + 8);
            } else {
                ctx.fillStyle = color;
                ctx.textBaseline = "bottom";
                ctx.fillText(label, bar.x, barTop - 4);
            }
        });
        ctx.restore();
    },
};

class DashboardBarChart extends Component {
    static template = "store_operation_requests.DashboardBarChart";
    static props = {
        title: String,
        labels: Array,
        values: Array,
        colors: Array,
        decimals: { type: Number, optional: true },
        onBarClick: Function,
    };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;
        useEffect(
            () => {
                this.renderChart();
                return () => {
                    if (this.chart) {
                        this.chart.destroy();
                        this.chart = null;
                    }
                };
            },
            () => [this.props.values, this.props.labels, this.props.decimals, this.canvasRef.el]
        );
    }

    renderChart() {
        if (!this.canvasRef.el) {
            return;
        }
        if (this.chart) {
            this.chart.destroy();
        }
        this.chart = new Chart(this.canvasRef.el, {
            type: "bar",
            data: {
                labels: this.props.labels,
                datasets: [
                    {
                        data: this.props.values,
                        backgroundColor: this.props.colors,
                        borderRadius: 6,
                        maxBarThickness: 56,
                    },
                ],
            },
            plugins: [barValueLabels],
            options: {
                maintainAspectRatio: false,
                layout: { padding: { top: 20 } },
                plugins: {
                    legend: { display: false },
                    barValueLabels: { decimals: this.props.decimals || 0 },
                },
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, grid: { color: "rgba(128, 128, 128, 0.15)" } },
                },
                onClick: (event, elements) => {
                    if (elements.length) {
                        this.props.onBarClick(elements[0].index);
                    }
                },
                onHover: (event, elements) => {
                    event.native.target.style.cursor = elements.length ? "pointer" : "default";
                },
            },
        });
    }
}

export class StoreOperationDashboard extends Component {
    static template = "store_operation_requests.Dashboard";
    static components = { ControlPanel, Dropdown, DropdownItem, DashboardBarChart };
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");

        const [dateFrom, dateTo] = presetRange("last_30_days");
        this.state = useState({
            issue: {},
            ret: {},
            deadlinePassedCount: 0,
            employees: [],
            departments: [],
            users: [],
            filters: {
                range: "last_30_days",
                dateFrom: serializeDate(dateFrom),
                dateTo: serializeDate(dateTo),
                employeeId: false,
                deptId: false,
                userId: false,
            },
        });

        onWillStart(async () => {
            await Promise.all([this.loadFilterOptions(), loadBundle("web.chartjs_lib")]);
            await this.loadAll();
        });
    }

    async loadFilterOptions() {
        // Derive filter options from the Issue/Return requests the current
        // user can actually see, rather than every hr.employee/hr.department/
        // res.users in the company: employee.purchase.requisition and
        // employee.return.request already carry the right record rules
        // (Requisition Manager = unrestricted, Department Head = own
        // department's requests, Requisition User = own submissions only),
        // so this naturally gives a Manager the full list and everyone else
        // only what's relevant to them, with no role check needed here.
        const [issueEmp, retEmp, issueDept, retDept, issueUser, retUser] = await Promise.all([
            this.orm.formattedReadGroup("employee.purchase.requisition", [], ["employee_id"], ["__count"]),
            this.orm.formattedReadGroup("employee.return.request", [], ["employee_id"], ["__count"]),
            this.orm.formattedReadGroup("employee.purchase.requisition", [], ["dept_id"], ["__count"]),
            this.orm.formattedReadGroup("employee.return.request", [], ["dept_id"], ["__count"]),
            this.orm.formattedReadGroup("employee.purchase.requisition", [], ["user_id"], ["__count"]),
            this.orm.formattedReadGroup("employee.return.request", [], ["user_id"], ["__count"]),
        ]);
        this.state.employees = this.dedupeOptions([...issueEmp, ...retEmp], "employee_id");
        this.state.departments = this.dedupeOptions([...issueDept, ...retDept], "dept_id");
        this.state.users = this.dedupeOptions([...issueUser, ...retUser], "user_id");
    }

    dedupeOptions(groups, field) {
        const byId = new Map();
        for (const g of groups) {
            const value = g[field];
            if (value) {
                byId.set(value[0], { id: value[0], name: value[1] });
            }
        }
        return [...byId.values()].sort((a, b) => a.name.localeCompare(b.name));
    }

    get baseDomain() {
        const f = this.state.filters;
        const domain = [
            ["requisition_date", ">=", f.dateFrom],
            ["requisition_date", "<=", f.dateTo],
        ];
        if (f.employeeId) {
            domain.push(["employee_id", "=", f.employeeId]);
        }
        if (f.deptId) {
            domain.push(["dept_id", "=", f.deptId]);
        }
        if (f.userId) {
            domain.push(["user_id", "=", f.userId]);
        }
        return domain;
    }

    async loadAll() {
        await Promise.all([this.loadCounts(), this.loadDeadlinePassed()]);
    }

    async loadCounts() {
        const domain = this.baseDomain;
        const [issueGroups, returnGroups] = await Promise.all([
            this.orm.formattedReadGroup(
                "employee.purchase.requisition", domain, ["state"], ["__count"]
            ),
            this.orm.formattedReadGroup(
                "employee.return.request", domain, ["state"], ["__count"]
            ),
        ]);
        const issueCounts = {};
        for (const g of issueGroups) {
            issueCounts[g.state] = g.__count;
        }
        const returnCounts = {};
        for (const g of returnGroups) {
            returnCounts[g.state] = g.__count;
        }
        this.state.issue = issueCounts;
        this.state.ret = returnCounts;
    }

    get deadlinePassedDomain() {
        return [
            ...this.baseDomain,
            ["requisition_deadline", "!=", false],
            ["requisition_deadline", "<", serializeDate(today())],
            ["state", "not in", ["received", "cancelled"]],
        ];
    }

    async loadDeadlinePassed() {
        this.state.deadlinePassedCount = await this.orm.searchCount(
            "employee.purchase.requisition", this.deadlinePassedDomain
        );
    }

    get issueStates() {
        return ISSUE_STATES.map((s) => ({ ...s, count: this.state.issue[s.key] || 0 }));
    }

    get returnStates() {
        return RETURN_STATES.map((s) => ({ ...s, count: this.state.ret[s.key] || 0 }));
    }

    get issueTotal() {
        return this.issueStates.reduce((sum, s) => sum + s.count, 0);
    }

    get returnTotal() {
        return this.returnStates.reduce((sum, s) => sum + s.count, 0);
    }

    // KPI tiles: a leading "Total" tile (mirrors the Sales dashboard, whose
    // first card is the plain order count) followed by one tile per state,
    // plus a Deadline Passed tile up front when there's anything overdue.
    get issueTiles() {
        const tiles = [
            {
                key: "total",
                label: "Total Issue Requests",
                icon: "fa-list-alt",
                color: "blue",
                count: this.issueTotal,
                onClick: () => this.openIssue(false),
            },
        ];
        if (this.state.deadlinePassedCount) {
            tiles.push({
                key: "deadline_passed",
                label: "Deadline Passed",
                icon: "fa-exclamation-triangle",
                color: "red",
                count: this.state.deadlinePassedCount,
                onClick: () => this.openDeadlinePassed(),
            });
        }
        for (const s of this.issueStates) {
            tiles.push({ ...s, onClick: () => this.openIssue(s.key) });
        }
        return tiles;
    }

    get returnTiles() {
        const tiles = [
            {
                key: "total",
                label: "Total Return Requests",
                icon: "fa-undo",
                color: "blue",
                count: this.returnTotal,
                onClick: () => this.openReturn(false),
            },
        ];
        for (const s of this.returnStates) {
            tiles.push({ ...s, onClick: () => this.openReturn(s.key) });
        }
        return tiles;
    }

    get issueChart() {
        return {
            kind: "issue",
            title: "Issue Requests Status",
            labels: ISSUE_STATES.map((s) => s.label),
            keys: ISSUE_STATES.map((s) => s.key),
            values: this.issueStates.map((s) => s.count),
            colors: ISSUE_STATES.map((s) => COLOR_HEX[s.color]),
        };
    }

    get returnChart() {
        return {
            kind: "return",
            title: "Return Requests Status",
            labels: RETURN_STATES.map((s) => s.label),
            keys: RETURN_STATES.map((s) => s.key),
            values: this.returnStates.map((s) => s.count),
            colors: RETURN_STATES.map((s) => COLOR_HEX[s.color]),
        };
    }

    onChartBarClick(chart, index) {
        const key = chart.keys[index];
        if (chart.kind === "issue") {
            this.openIssue(key);
        } else {
            this.openReturn(key);
        }
    }

    get presets() {
        return DATE_PRESETS;
    }

    get currentLabel() {
        const f = this.state.filters;
        if (f.range === "custom") {
            return `${f.dateFrom} to ${f.dateTo}`;
        }
        const preset = DATE_PRESETS.find((p) => p.id === f.range);
        return preset ? preset.label : "";
    }

    isSelected(range) {
        return this.state.filters.range === range;
    }

    selectPreset(range) {
        const [dateFrom, dateTo] = presetRange(range);
        this.state.filters.range = range;
        this.state.filters.dateFrom = serializeDate(dateFrom);
        this.state.filters.dateTo = serializeDate(dateTo);
        this.loadAll();
    }

    selectCustom() {
        this.state.filters.range = "custom";
    }

    onCustomDateChange(field, ev) {
        this.state.filters[field] = ev.target.value;
        if (this.state.filters.dateFrom && this.state.filters.dateTo) {
            this.loadAll();
        }
    }

    onEmployeeChange(ev) {
        this.state.filters.employeeId = ev.target.value ? parseInt(ev.target.value, 10) : false;
        this.loadAll();
    }

    onDeptChange(ev) {
        this.state.filters.deptId = ev.target.value ? parseInt(ev.target.value, 10) : false;
        this.loadAll();
    }

    onUserChange(ev) {
        this.state.filters.userId = ev.target.value ? parseInt(ev.target.value, 10) : false;
        this.loadAll();
    }

    openIssue(state) {
        const domain = state ? [...this.baseDomain, ["state", "=", state]] : this.baseDomain;
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Issue Requests",
            res_model: "employee.purchase.requisition",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }

    openReturn(state) {
        const domain = state ? [...this.baseDomain, ["state", "=", state]] : this.baseDomain;
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Return Requests",
            res_model: "employee.return.request",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }

    openDeadlinePassed() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Deadline Passed",
            res_model: "employee.purchase.requisition",
            views: [[false, "list"], [false, "form"]],
            domain: this.deadlinePassedDomain,
        });
    }
}

registry.category("actions").add("store_operation_dashboard", StoreOperationDashboard);
