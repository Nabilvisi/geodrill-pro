import React, { useEffect, useState, useCallback } from 'react';
import {
  ChevronRight,
  ChevronDown,
  Plus,
  Folder,
  Layers,
  Crosshair,
  Target as TargetIcon,
  Compass,
  Check,
  AlertCircle,
  X
} from 'lucide-react';
import { api } from '../api';

export interface TargetModel {
  id: string;
  name: string;
  geometry_type: string;
  center_tvd_m: number;
  center_north_m: number;
  center_east_m: number;
  radius_m: number;
  tolerance_m: number;
}

export interface WellboreModel {
  id: string;
  well_id: string;
  name: string;
  uwi: string;
  wellbore_type: 'original' | 'sidetrack' | 'bypass' | 'reentry';
  sidetrack_parent_id?: string | null;
  kickoff_md_m: number;
  planned_td_m: number;
  targets: TargetModel[];
}

export interface WellModel {
  id: string;
  project_id: string;
  field_id?: string | null;
  name: string;
  uwi: string;
  wellbores: WellboreModel[];
}

export interface FieldModel {
  id: string;
  name: string;
  basin: string;
  country: string;
  wells: WellModel[];
}

export interface ProjectTreeData {
  project: {
    id: string;
    name: string;
    datum: string;
  };
  fields: FieldModel[];
  unassigned_wells: WellModel[];
}

interface ProjectTreeProps {
  projectId: string;
  activeWellId?: string;
  activeWellboreId?: string;
  onSelectWell?: (well: WellModel) => void;
  onSelectWellbore?: (wellbore: WellboreModel, well: WellModel) => void;
  className?: string;
}

export const ProjectTree: React.FC<ProjectTreeProps> = ({
  projectId,
  activeWellId,
  activeWellboreId,
  onSelectWell,
  onSelectWellbore,
  className = '',
}) => {
  const [tree, setTree] = useState<ProjectTreeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  // Modal states for creating nodes
  const [modalType, setModalType] = useState<'field' | 'well' | 'wellbore' | 'target' | null>(null);
  const [targetParentId, setTargetParentId] = useState<string>('');
  const [formName, setFormName] = useState('');
  const [formExtra1, setFormExtra1] = useState('');
  const [formExtra2, setFormExtra2] = useState('');
  const [formNum1, setFormNum1] = useState<number>(0);
  const [formNum2, setFormNum2] = useState<number>(0);

  const fetchTree = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await api<ProjectTreeData>(`/v1/projects/${projectId}/tree`);
      setTree(data);
      // Auto-expand fields and wells
      const newExpanded: Record<string, boolean> = { ...expanded };
      data.fields.forEach(f => {
        newExpanded[`field-${f.id}`] = true;
        f.wells.forEach(w => {
          newExpanded[`well-${w.id}`] = true;
        });
      });
      data.unassigned_wells.forEach(w => {
        newExpanded[`well-${w.id}`] = true;
      });
      setExpanded(newExpanded);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      fetchTree();
    }
  }, [projectId, fetchTree]);

  const toggleExpand = (key: string) => {
    setExpanded(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (modalType === 'field') {
        await api(`/v1/projects/${projectId}/fields`, {
          method: 'POST',
          body: JSON.stringify({ name: formName, basin: formExtra1, country: formExtra2 }),
          headers: { 'Content-Type': 'application/json' },
        });
      } else if (modalType === 'well') {
        await api(`/v1/projects/${projectId}/wells`, {
          method: 'POST',
          body: JSON.stringify({
            name: formName,
            uwi: formExtra1,
            field_id: targetParentId || null,
          }),
          headers: { 'Content-Type': 'application/json' },
        });
      } else if (modalType === 'wellbore') {
        await api(`/v1/wells/${targetParentId}/wellbores`, {
          method: 'POST',
          body: JSON.stringify({
            name: formName,
            uwi: formExtra1,
            wellbore_type: formExtra2 || 'original',
            kickoff_md_m: formNum1,
            planned_td_m: formNum2,
          }),
          headers: { 'Content-Type': 'application/json' },
        });
      } else if (modalType === 'target') {
        await api(`/v1/wellbores/${targetParentId}/targets`, {
          method: 'POST',
          body: JSON.stringify({
            name: formName,
            center_tvd_m: formNum1,
            radius_m: formNum2 || 50,
            geometry_type: 'circle',
          }),
          headers: { 'Content-Type': 'application/json' },
        });
      }
      setModalType(null);
      setFormName('');
      setFormExtra1('');
      setFormExtra2('');
      setFormNum1(0);
      setFormNum2(0);
      await fetchTree();
    } catch (err) {
      alert(`Error creating entity: ${(err as Error).message}`);
    }
  };

  const renderWellbore = (wb: WellboreModel, well: WellModel) => {
    const isWbActive = activeWellboreId === wb.id;
    const isExpanded = expanded[`wb-${wb.id}`];

    return (
      <div key={wb.id} style={{ marginLeft: '24px', marginBottom: '4px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '4px 8px',
            borderRadius: '4px',
            backgroundColor: isWbActive ? '#EFF6FF' : 'transparent',
            border: isWbActive ? '1px solid #3B82F6' : '1px solid transparent',
            cursor: 'pointer',
          }}
          onClick={() => {
            onSelectWellbore?.(wb, well);
            onSelectWell?.(well);
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {wb.targets && wb.targets.length > 0 ? (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleExpand(`wb-${wb.id}`);
                }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              >
                {isExpanded ? <ChevronDown size={14} color="#6B7280" /> : <ChevronRight size={14} color="#6B7280" />}
              </button>
            ) : (
              <span style={{ width: '14px' }} />
            )}
            <Compass size={14} color={isWbActive ? '#2563EB' : '#0EA5B7'} />
            <span style={{ fontSize: '12px', fontWeight: isWbActive ? 600 : 500, color: '#1F2937' }}>
              {wb.name}
            </span>
            <span
              style={{
                fontSize: '10px',
                padding: '1px 5px',
                borderRadius: '8px',
                backgroundColor: wb.wellbore_type === 'original' ? '#F3F4F6' : '#FEF3C7',
                color: wb.wellbore_type === 'original' ? '#4B5563' : '#92400E',
                textTransform: 'uppercase',
              }}
            >
              {wb.wellbore_type}
            </span>
          </div>
          <button
            type="button"
            title="Add Target"
            onClick={(e) => {
              e.stopPropagation();
              setTargetParentId(wb.id);
              setFormName('Target 1');
              setFormNum1(2500);
              setFormNum2(50);
              setModalType('target');
            }}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: '#9CA3AF',
              padding: '2px',
            }}
          >
            <Plus size={13} />
          </button>
        </div>

        {/* Targets under wellbore */}
        {isExpanded && wb.targets && wb.targets.length > 0 && (
          <div style={{ marginLeft: '24px', marginTop: '2px', borderLeft: '1px dashed #E5E7EB', paddingLeft: '8px' }}>
            {wb.targets.map(t => (
              <div
                key={t.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '2px 4px',
                  fontSize: '11px',
                  color: '#4B5563',
                }}
              >
                <TargetIcon size={12} color="#F97316" />
                <span>{t.name}</span>
                <span style={{ color: '#9CA3AF', fontSize: '10px' }}>({t.center_tvd_m} m TVD · r={t.radius_m}m)</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderWell = (well: WellModel) => {
    const isWellActive = activeWellId === well.id;
    const isExpanded = expanded[`well-${well.id}`];

    return (
      <div key={well.id} style={{ marginLeft: '16px', marginBottom: '6px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '5px 8px',
            borderRadius: '4px',
            backgroundColor: isWellActive && !activeWellboreId ? '#F0FDF4' : 'transparent',
            cursor: 'pointer',
          }}
          onClick={() => {
            onSelectWell?.(well);
            toggleExpand(`well-${well.id}`);
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                toggleExpand(`well-${well.id}`);
              }}
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
            >
              {isExpanded ? <ChevronDown size={14} color="#6B7280" /> : <ChevronRight size={14} color="#6B7280" />}
            </button>
            <Layers size={14} color="#1E3A8A" />
            <strong style={{ fontSize: '12px', color: '#111827' }}>{well.name}</strong>
            {well.uwi && <span style={{ fontSize: '10px', color: '#6B7280' }}>({well.uwi})</span>}
          </div>
          <button
            type="button"
            title="Add Wellbore"
            onClick={(e) => {
              e.stopPropagation();
              setTargetParentId(well.id);
              setFormName(`${well.name} WB01`);
              setFormExtra1('');
              setFormExtra2('original');
              setFormNum1(0);
              setFormNum2(3000);
              setModalType('wellbore');
            }}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: '#6B7280',
              padding: '2px',
            }}
          >
            <Plus size={14} />
          </button>
        </div>

        {isExpanded && well.wellbores && (
          <div style={{ marginTop: '2px' }}>
            {well.wellbores.map(wb => renderWellbore(wb, well))}
            {well.wellbores.length === 0 && (
              <div style={{ marginLeft: '32px', fontSize: '11px', color: '#9CA3AF', fontStyle: 'italic' }}>
                No wellbores defined
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      className={`project-tree-container ${className}`}
      style={{
        backgroundColor: '#FFFFFF',
        border: '1px solid #E5E7EB',
        borderRadius: '8px',
        padding: '12px',
        fontSize: '13px',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '10px',
          borderBottom: '1px solid #F3F4F6',
          paddingBottom: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Folder size={16} color="#1E3A8A" />
          <strong style={{ color: '#1E3A8A', fontSize: '13px' }}>
            {tree?.project.name ?? 'Well Hierarchy'}
          </strong>
        </div>
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            type="button"
            className="button secondary"
            style={{ padding: '2px 8px', fontSize: '11px' }}
            onClick={() => {
              setFormName('');
              setFormExtra1('');
              setFormExtra2('');
              setModalType('field');
            }}
          >
            <Plus size={12} /> Field
          </button>
          <button
            type="button"
            className="button secondary"
            style={{ padding: '2px 8px', fontSize: '11px' }}
            onClick={() => {
              setTargetParentId('');
              setFormName('');
              setFormExtra1('');
              setModalType('well');
            }}
          >
            <Plus size={12} /> Well
          </button>
        </div>
      </div>

      {loading && <div style={{ color: '#6B7280', fontSize: '12px', padding: '8px' }}>Loading hierarchy...</div>}
      {error && <div style={{ color: '#EF4444', fontSize: '12px', padding: '8px' }}>{error}</div>}

      {tree && (
        <div className="tree-content">
          {/* Fields */}
          {tree.fields.map(field => {
            const isExpanded = expanded[`field-${field.id}`];
            return (
              <div key={field.id} style={{ marginBottom: '8px' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '4px 6px',
                    borderRadius: '4px',
                    backgroundColor: '#F9FAFB',
                    cursor: 'pointer',
                  }}
                  onClick={() => toggleExpand(`field-${field.id}`)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleExpand(`field-${field.id}`);
                      }}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                    >
                      {isExpanded ? <ChevronDown size={14} color="#4B5563" /> : <ChevronRight size={14} color="#4B5563" />}
                    </button>
                    <Crosshair size={14} color="#0D9488" />
                    <span style={{ fontWeight: 600, color: '#374151', fontSize: '12px' }}>
                      {field.name}
                    </span>
                    {field.basin && <span style={{ fontSize: '10px', color: '#9CA3AF' }}>• {field.basin}</span>}
                  </div>
                  <button
                    type="button"
                    title="Add Well to Field"
                    onClick={(e) => {
                      e.stopPropagation();
                      setTargetParentId(field.id);
                      setFormName('');
                      setFormExtra1('');
                      setModalType('well');
                    }}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6B7280' }}
                  >
                    <Plus size={13} />
                  </button>
                </div>

                {isExpanded && field.wells && (
                  <div style={{ marginTop: '4px' }}>
                    {field.wells.map(w => renderWell(w))}
                    {field.wells.length === 0 && (
                      <div style={{ marginLeft: '24px', fontSize: '11px', color: '#9CA3AF', fontStyle: 'italic' }}>
                        No wells in this field
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}

          {/* Unassigned Wells */}
          {tree.unassigned_wells && tree.unassigned_wells.length > 0 && (
            <div style={{ marginTop: '8px' }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: '#6B7280', padding: '2px 6px', textTransform: 'uppercase' }}>
                Unassigned Wells
              </div>
              {tree.unassigned_wells.map(w => renderWell(w))}
            </div>
          )}
        </div>
      )}

      {/* Creation Modal */}
      {modalType && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '8px',
              padding: '20px',
              width: '380px',
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ margin: 0, fontSize: '15px', color: '#111827' }}>
                Create {modalType.charAt(0).toUpperCase() + modalType.slice(1)}
              </h3>
              <button
                type="button"
                onClick={() => setModalType(null)}
                style={{ background: 'none', border: 'none', cursor: 'pointer' }}
              >
                <X size={16} />
              </button>
            </div>
            <form onSubmit={handleCreateSubmit}>
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#374151', marginBottom: '4px' }}>
                  Name
                </label>
                <input
                  type="text"
                  required
                  value={formName}
                  onChange={e => setFormName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 8px',
                    borderRadius: '4px',
                    border: '1px solid #D1D5DB',
                    fontSize: '13px',
                  }}
                />
              </div>

              {modalType === 'field' && (
                <>
                  <div style={{ marginBottom: '12px' }}>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#374151', marginBottom: '4px' }}>
                      Basin
                    </label>
                    <input
                      type="text"
                      value={formExtra1}
                      onChange={e => setFormExtra1(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '6px 8px',
                        borderRadius: '4px',
                        border: '1px solid #D1D5DB',
                        fontSize: '13px',
                      }}
                    />
                  </div>
                  <div style={{ marginBottom: '12px' }}>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#374151', marginBottom: '4px' }}>
                      Country
                    </label>
                    <input
                      type="text"
                      value={formExtra2}
                      onChange={e => setFormExtra2(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '6px 8px',
                        borderRadius: '4px',
                        border: '1px solid #D1D5DB',
                        fontSize: '13px',
                      }}
                    />
                  </div>
                </>
              )}

              {modalType === 'well' && (
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#374151', marginBottom: '4px' }}>
                    Unique Well Identifier (UWI)
                  </label>
                  <input
                    type="text"
                    value={formExtra1}
                    onChange={e => setFormExtra1(e.target.value)}
                    placeholder="e.g. 15/9-F-12"
                    style={{
                      width: '100%',
                      padding: '6px 8px',
                      borderRadius: '4px',
                      border: '1px solid #D1D5DB',
                      fontSize: '13px',
                    }}
                  />
                </div>
              )}

              {modalType === 'wellbore' && (
                <>
                  <div style={{ marginBottom: '12px' }}>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#374151', marginBottom: '4px' }}>
                      Wellbore Type
                    </label>
                    <select
                      value={formExtra2}
                      onChange={e => setFormExtra2(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '6px 8px',
                        borderRadius: '4px',
                        border: '1px solid #D1D5DB',
                        fontSize: '13px',
                      }}
                    >
                      <option value="original">Original Hole</option>
                      <option value="sidetrack">Sidetrack</option>
                      <option value="bypass">Bypass</option>
                      <option value="reentry">Re-entry</option>
                    </select>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#374151', marginBottom: '4px' }}>
                        Kickoff MD (m)
                      </label>
                      <input
                        type="number"
                        step="any"
                        value={formNum1}
                        onChange={e => setFormNum1(parseFloat(e.target.value) || 0)}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          borderRadius: '4px',
                          border: '1px solid #D1D5DB',
                          fontSize: '13px',
                        }}
                      />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#374151', marginBottom: '4px' }}>
                        Planned TD (m)
                      </label>
                      <input
                        type="number"
                        step="any"
                        value={formNum2}
                        onChange={e => setFormNum2(parseFloat(e.target.value) || 0)}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          borderRadius: '4px',
                          border: '1px solid #D1D5DB',
                          fontSize: '13px',
                        }}
                      />
                    </div>
                  </div>
                </>
              )}

              {modalType === 'target' && (
                <>
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#374151', marginBottom: '4px' }}>
                        Center TVD (m)
                      </label>
                      <input
                        type="number"
                        step="any"
                        required
                        value={formNum1}
                        onChange={e => setFormNum1(parseFloat(e.target.value) || 0)}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          borderRadius: '4px',
                          border: '1px solid #D1D5DB',
                          fontSize: '13px',
                        }}
                      />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#374151', marginBottom: '4px' }}>
                        Radius (m)
                      </label>
                      <input
                        type="number"
                        step="any"
                        required
                        value={formNum2}
                        onChange={e => setFormNum2(parseFloat(e.target.value) || 50)}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          borderRadius: '4px',
                          border: '1px solid #D1D5DB',
                          fontSize: '13px',
                        }}
                      />
                    </div>
                  </div>
                </>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '16px' }}>
                <button
                  type="button"
                  className="button secondary"
                  onClick={() => setModalType(null)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="button primary"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
