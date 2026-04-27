"""
Validators - Validação de entrada e sanitização de dados
"""
import re
from typing import Optional, Any, Dict, List
from datetime import datetime, date
from config.constants import (
    TELEFONE_REGEX, 
    EMAIL_REGEX, 
    CNPJ_REGEX, 
    CPF_REGEX,
    EXTENSOES_PERMITIDAS
)


class ValidationError(Exception):
    """Exceção customizada para erros de validação"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class Validator:
    """Classe para validação de dados"""
    
    @staticmethod
    def required(value: Any, field_name: str) -> Any:
        """Valida que o campo não está vazio"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(field_name, "Campo obrigatório")
        return value
    
    @staticmethod
    def string(value: Any, field_name: str, min_length: int = 0, max_length: Optional[int] = None) -> str:
        """Valida string com tamanho mínimo e máximo"""
        if not isinstance(value, str):
            raise ValidationError(field_name, "Deve ser uma string")
        
        value = value.strip()
        
        if len(value) < min_length:
            raise ValidationError(field_name, f"Tamanho mínimo: {min_length} caracteres")
        
        if max_length and len(value) > max_length:
            raise ValidationError(field_name, f"Tamanho máximo: {max_length} caracteres")
        
        return value
    
    @staticmethod
    def email(value: str, field_name: str = "email") -> str:
        """Valida formato de email"""
        value = Validator.string(value, field_name, min_length=5, max_length=200)
        
        if not re.match(EMAIL_REGEX, value):
            raise ValidationError(field_name, "Formato de email inválido")
        
        return value.lower()
    
    @staticmethod
    def telefone(value: str, field_name: str = "telefone") -> str:
        """Valida formato de telefone (apenas dígitos)"""
        # Remove caracteres não numéricos
        digits = re.sub(r'\D', '', value)
        
        if not re.match(TELEFONE_REGEX, digits):
            raise ValidationError(field_name, "Telefone deve ter entre 10 e 15 dígitos")
        
        return digits
    
    @staticmethod
    def cpf(value: str, field_name: str = "cpf") -> str:
        """Valida formato de CPF"""
        digits = re.sub(r'\D', '', value)
        
        if not re.match(CPF_REGEX, digits):
            raise ValidationError(field_name, "CPF deve ter 11 dígitos")
        
        return digits
    
    @staticmethod
    def cnpj(value: str, field_name: str = "cnpj") -> str:
        """Valida formato de CNPJ"""
        digits = re.sub(r'\D', '', value)
        
        if not re.match(CNPJ_REGEX, digits):
            raise ValidationError(field_name, "CNPJ deve ter 14 dígitos")
        
        return digits
    
    @staticmethod
    def integer(value: Any, field_name: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
        """Valida número inteiro"""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(field_name, "Deve ser um número inteiro")
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(field_name, f"Valor mínimo: {min_value}")
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(field_name, f"Valor máximo: {max_value}")
        
        return int_value
    
    @staticmethod
    def float_value(value: Any, field_name: str, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
        """Valida número decimal"""
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(field_name, "Deve ser um número")
        
        if min_value is not None and float_value < min_value:
            raise ValidationError(field_name, f"Valor mínimo: {min_value}")
        
        if max_value is not None and float_value > max_value:
            raise ValidationError(field_name, f"Valor máximo: {max_value}")
        
        return float_value
    
    @staticmethod
    def date_string(value: str, field_name: str, format: str = "%Y-%m-%d") -> date:
        """Valida e converte string de data"""
        try:
            return datetime.strptime(value, format).date()
        except ValueError:
            raise ValidationError(field_name, f"Data inválida. Formato esperado: {format}")
    
    @staticmethod
    def choice(value: Any, field_name: str, choices: List[Any]) -> Any:
        """Valida que o valor está entre as opções permitidas"""
        if value not in choices:
            raise ValidationError(field_name, f"Opção inválida. Valores permitidos: {', '.join(map(str, choices))}")
        
        return value
    
    @staticmethod
    def file_extension(filename: str, field_name: str = "arquivo") -> str:
        """Valida extensão de arquivo"""
        import os
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in EXTENSOES_PERMITIDAS:
            raise ValidationError(
                field_name, 
                f"Extensão não permitida. Permitidas: {', '.join(EXTENSOES_PERMITIDAS)}"
            )
        
        return ext
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """Remove tags HTML perigosas (sanitização básica)"""
        import html
        # Escape HTML
        return html.escape(value)
    
    @staticmethod
    def nps_score(value: Any, field_name: str = "nps_nota") -> int:
        """Valida nota NPS (0-10)"""
        return Validator.integer(value, field_name, min_value=0, max_value=10)


def validate_cliente_data(data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
    """
    Valida dados de cliente (cadastro/edição)
    
    Args:
        data: Dicionário com dados do formulário
        is_update: Se True, campos obrigatórios podem ser opcionais
    
    Returns:
        Dicionário com dados validados
    
    Raises:
        ValidationError: Se algum campo for inválido
    """
    validated = {}
    
    # Campos obrigatórios
    if not is_update or 'nome' in data:
        validated['nome'] = Validator.string(
            Validator.required(data.get('nome'), 'nome'),
            'nome',
            min_length=2,
            max_length=100
        )
    
    if not is_update or 'telefone' in data:
        validated['telefone'] = Validator.telefone(
            Validator.required(data.get('telefone'), 'telefone'),
            'telefone'
        )
    
    # Email opcional
    if 'email' in data and data.get('email'):
        validated['email'] = Validator.email(data['email'], 'email')
    
    # Tipo pessoa
    if not is_update or 'tipo_pessoa' in data:
        from config.constants import TipoPessoa
        tipo_choices = [t.value for t in TipoPessoa]
        validated['tipo_pessoa'] = Validator.choice(
            data.get('tipo_pessoa', 'Cliente'),
            'tipo_pessoa',
            tipo_choices
        )
    
    # Campos específicos de pessoa física
    if data.get('tipo_pessoa') == 'Física':
        if 'renda' in data and data.get('renda'):
            validated['renda'] = Validator.float_value(data['renda'], 'renda', min_value=0)
        
        if 'data_nascimento' in data and data.get('data_nascimento'):
            validated['data_nascimento'] = Validator.date_string(data['data_nascimento'], 'data_nascimento')
    
    # Campos específicos de pessoa jurídica
    if data.get('tipo_pessoa') == 'Jurídica':
        if 'faturamento' in data and data.get('faturamento'):
            validated['faturamento'] = Validator.float_value(data['faturamento'], 'faturamento', min_value=0)
        
        if 'qtd_funcionarios' in data and data.get('qtd_funcionarios'):
            validated['qtd_funcionarios'] = Validator.integer(data['qtd_funcionarios'], 'qtd_funcionarios', min_value=0)
        
        if 'data_abertura' in data and data.get('data_abertura'):
            validated['data_abertura'] = Validator.date_string(data['data_abertura'], 'data_abertura')
    
    # Observações (sanitizar)
    if 'observacoes' in data and data.get('observacoes'):
        validated['observacoes'] = Validator.sanitize_html(data['observacoes'])
    
    return validated


def validate_mesa_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Valida dados de mesa de negócio"""
    validated = {}
    
    validated['topico'] = Validator.string(
        Validator.required(data.get('topico'), 'topico'),
        'topico',
        min_length=3,
        max_length=150
    )
    
    validated['produtos'] = Validator.string(
        Validator.required(data.get('produtos'), 'produtos'),
        'produtos',
        min_length=1,
        max_length=250
    )
    
    from config.constants import SituacaoMesa
    situacao_choices = [s.value for s in SituacaoMesa]
    validated['situacao'] = Validator.choice(
        Validator.required(data.get('situacao'), 'situacao'),
        'situacao',
        situacao_choices
    )
    
    if 'valor_total' in data:
        validated['valor_total'] = Validator.float_value(
            data['valor_total'],
            'valor_total',
            min_value=0
        )
    
    if 'descricao' in data and data.get('descricao'):
        validated['descricao'] = Validator.sanitize_html(data['descricao'])
    
    return validated
