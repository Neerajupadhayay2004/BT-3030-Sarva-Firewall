import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Tooltip, 
  Legend,
  Sector
} from "recharts";
import { ShieldAlert } from "lucide-react";
import { useState } from "react";

const COLORS = [
  'hsl(var(--primary))',
  'hsl(var(--destructive))',
  'hsl(var(--warning))',
  'hsl(var(--success))',
  'hsl(var(--accent))',
  '#a855f7', // Purple
  '#06b6d4', // Cyan
  '#f97316', // Orange
];

const renderActiveShape = (props: any) => {
  const RADIAN = Math.PI / 180;
  const { cx, cy, midAngle, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent, value } = props;
  const sin = Math.sin(-RADIAN * midAngle);
  const cos = Math.cos(-RADIAN * midAngle);
  const sx = cx + (outerRadius + 10) * cos;
  const sy = cy + (outerRadius + 10) * sin;
  const mx = cx + (outerRadius + 30) * cos;
  const my = cy + (outerRadius + 30) * sin;
  const ex = mx + (cos >= 0 ? 1 : -1) * 22;
  const ey = my;
  const textAnchor = cos >= 0 ? 'start' : 'end';

  return (
    <g>
      <text x={cx} y={cy} dy={8} textAnchor="middle" fill={fill} className="text-sm font-bold">
        {payload.name}
      </text>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
      />
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={outerRadius + 6}
        outerRadius={outerRadius + 10}
        fill={fill}
      />
      <path d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`} stroke={fill} fill="none" />
      <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
      <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} textAnchor={textAnchor} fill="hsl(var(--foreground))" className="text-xs">
        {`${value} attacks`}
      </text>
      <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} dy={18} textAnchor={textAnchor} fill="hsl(var(--muted-foreground))" className="text-[10px]">
        {`(${(percent * 100).toFixed(1)}%)`}
      </text>
    </g>
  );
};

const AttackDistribution = ({ data }: any) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const attackCategories = data?.attack_categories ?? {};

  const totalAttacks = Object.values(attackCategories).reduce(
    (sum: number, attacks: any) => sum + Object.keys(attacks).length, 
    0
  );

  const categories = Object.entries(attackCategories)
    .map(([type, attacks]: any) => ({
      name: type.toUpperCase().replace(/_/g, " "),
      value: Object.keys(attacks).length,
    }))
    .filter(item => item.value > 0)
    .sort((a, b) => b.value - a.value);

  const onPieEnter = (_: any, index: number) => {
    setActiveIndex(index);
  };

  return (
    <Card className="cyber-border bg-card/50 backdrop-blur-sm h-full min-h-[450px]">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xl font-bold text-foreground flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-primary" />
          Top Attack Categories
        </CardTitle>
        <Badge variant="outline" className="border-primary/50 text-primary">
          {categories.length} Types
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="h-[350px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <defs>
                {COLORS.map((color, index) => (
                  <filter key={`filter-${index}`} id={`shadow-${index}`}>
                    <feGaussianBlur in="SourceAlpha" stdDeviation="2" result="blur" />
                    <feOffset in="blur" dx="0" dy="0" result="offsetBlur" />
                    <feFlood floodColor={color} floodOpacity="0.5" result="offsetColor" />
                    <feComposite in="offsetColor" in2="offsetBlur" operator="in" result="offsetBlur" />
                    <feMerge>
                      <feMergeNode />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                ))}
              </defs>
              <Pie
                activeIndex={activeIndex}
                activeShape={renderActiveShape}
                data={categories}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={95}
                dataKey="value"
                onMouseEnter={onPieEnter}
                paddingAngle={4}
                stroke="none"
              >
                {categories.map((_, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={COLORS[index % COLORS.length]} 
                    style={{ filter: activeIndex === index ? `url(#shadow-${index})` : 'none' }}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--primary))',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                }}
              />
              <Legend 
                verticalAlign="bottom" 
                height={36} 
                iconType="circle"
                formatter={(value: string) => (
                  <span className="text-xs font-medium text-muted-foreground">{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 flex justify-center items-center gap-6 text-xs border-t border-border pt-4">
          <div className="flex flex-col items-center">
            <span className="text-muted-foreground uppercase tracking-wider text-[10px]">Total Attacks</span>
            <span className="text-xl font-bold text-primary">{totalAttacks as number}</span>
          </div>
          <div className="w-[1px] h-8 bg-border" />
          <div className="flex flex-col items-center">
            <span className="text-muted-foreground uppercase tracking-wider text-[10px]">Highest Risk</span>
            <span className="text-xl font-bold text-destructive">{(categories[0]?.name as string) || 'N/A'}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AttackDistribution;
