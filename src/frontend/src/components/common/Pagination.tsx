import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { PaginationMeta } from '../../types/api';

interface PaginationProps {
  pagination: PaginationMeta;
  onPageChange: (newPage: number) => void;
  disabled?: boolean;
}

export const Pagination: React.FC<PaginationProps> = ({
  pagination,
  onPageChange,
  disabled = false,
}) => {
  const { page, total_pages, total, page_size } = pagination;

  const startItem = total === 0 ? 0 : (page - 1) * page_size + 1;
  const endItem = Math.min(page * page_size, total);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.75rem 1rem',
        borderTop: '1px solid #e2e8f0',
        backgroundColor: '#ffffff',
        fontSize: '0.875rem',
        color: '#475569',
        flexWrap: 'wrap',
        gap: '0.75rem',
      }}
    >
      <div>
        Showing <span style={{ fontWeight: 600, color: '#0f172a' }}>{startItem.toLocaleString()}</span> to{' '}
        <span style={{ fontWeight: 600, color: '#0f172a' }}>{endItem.toLocaleString()}</span> of{' '}
        <span style={{ fontWeight: 600, color: '#0f172a' }}>{total.toLocaleString()}</span> records
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
        <button
          className="btn btn-sm btn-secondary"
          onClick={() => onPageChange(1)}
          disabled={disabled || page <= 1}
          aria-label="First Page"
          title="First Page"
        >
          <ChevronsLeft size={14} />
        </button>
        <button
          className="btn btn-sm btn-secondary"
          onClick={() => onPageChange(page - 1)}
          disabled={disabled || page <= 1}
          aria-label="Previous Page"
          title="Previous Page"
        >
          <ChevronLeft size={14} />
        </button>

        <span style={{ padding: '0 0.5rem', fontWeight: 500, fontSize: '0.8125rem' }}>
          Page {page} of {Math.max(1, total_pages)}
        </span>

        <button
          className="btn btn-sm btn-secondary"
          onClick={() => onPageChange(page + 1)}
          disabled={disabled || page >= total_pages}
          aria-label="Next Page"
          title="Next Page"
        >
          <ChevronRight size={14} />
        </button>
        <button
          className="btn btn-sm btn-secondary"
          onClick={() => onPageChange(total_pages)}
          disabled={disabled || page >= total_pages}
          aria-label="Last Page"
          title="Last Page"
        >
          <ChevronsRight size={14} />
        </button>
      </div>
    </div>
  );
};
